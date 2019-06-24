# pylint: disable=c0111, r1705, w1203

from pathlib import Path
import subprocess
import hashlib
import re

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden

from nbh_main.settings import sitesettings
from nbh_main.settings import logger, DEBUG
from nbhosting.stats.stats import Stats

# Create your views here.


def error_page(request, course, student, notebook, message=None):
    return render(
        request, "error.html", dict(
            course=course, student=student,
            notebook=notebook, message=message))


def log_completed_process(completed_process, subcommand):
    header = f"{10 * '='} {subcommand}"
    logger.info(f"{header} returned ==> {completed_process.returncode}")
    for field in ('stdout', 'stderr'):
        text = getattr(completed_process, field, 'undef')
        # nothing to show
        if not text:
            continue
        # implement policy for stderr
        if field == 'stderr':
            # config has requested to not log stderr at all
            if sitesettings.log_subprocess_stderr is None:
                continue
            # config requires stderr only for failed subprocesses
            if sitesettings.log_subprocess_stderr is False \
               and completed_process.returncode == 0:
                continue
        logger.info(f"{header} - {field}")
        logger.info(text)


# auth scheme here depends on the presence of META.HTTP_REFERER
# if present, check that one of the fields in 'allowed_referer_domains' appears in referer
# otherwise, performs check of META.REMOTE_ADDR against 'allowed_devel_ips'
def authorized(request):

    # check HTTP_REFERER against allowed_referer_domains
    def authorize_refered_request(request):
        # actual referer
        referer = request.META['HTTP_REFERER']
        domains = sitesettings.allowed_referer_domains
        result = any(domain in referer
                     for domain in domains)
        explanation = "HTTP_REFERER = {}, allowed_referer_domains = {}"\
                      .format(referer, domains)
        return result, explanation

    # check REMOTE_ADDR against allowed_devel_ips
    def authorize_devel_request(request):
        incoming_ip = request.META['REMOTE_ADDR']
        allowed_devel_ips = sitesettings.allowed_devel_ips
        result = False
        for mode, allowed in allowed_devel_ips:
            if mode == 'exact' and incoming_ip == allowed:
                result = True
            if mode == 'match' and re.match(allowed, incoming_ip):
                result = True
        explanation = "REMOTE_ADDR = {}, allowed_devel_ips = {}"\
                      .format(incoming_ip, allowed_devel_ips)
        return result, explanation


    # our result is always of the form
    # authorized, explanation
    # where explanation is relevant when authorized is False

    # inside an iframe ?
    if 'HTTP_REFERER' in request.META:
        return authorize_refered_request(request)
    else:
        return authorize_devel_request(request)

def edx_request(request, course, student, notebook):    # pylint: disable=r0914

    """
    the main edxfront entry point; it
    * creates a student if needed
    * copies the notebook if needed
    * makes sure the student container is ready to answer http requests
    and then returns a http redirect to /port/<notebook_path>
    """

    ok, explanation = authorized(request)

    if not ok:
        return HttpResponseForbidden(
            f"Access denied: {explanation}")

    # the ipynb extension is removed from the notebook name in urls.py
    notebook_withext = notebook + ".ipynb"
    # have we received a request to force the copy (for reset_from_origin)
    forcecopy = request.GET.get('forcecopy', False)

    subcommand = 'docker-view-student-course-notebook'

    # build command
    command = ['nbh', '-d', sitesettings.nbhroot]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)
    # propagate the forcecopy flag for reset_from_origin
    if forcecopy:
        command.append('-f')
    # propagate that a git initialization was requested
    # forcecopy has no effect in this case
    if init_student_git:
        command.append('-g')

    coursedir = CourseDir(course)
    if not coursedir.is_valid():
        return error_page(
            request, course, student, notebook,
            f"no such course {course}"
        )

    # add arguments to the subcommand
    command += [student, course, notebook_withext]
    logger.info(f'In {Path.cwd()}\n-> Running command {" ".join(command)}')
    completed_process = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed_process, subcommand)

    if completed_process.returncode != 0:
        message = "command {} returned {}\nstderr:{}"\
                  .format(" ".join(command),
                          completed_process.returncode,
                          completed_process.stderr)
        return error_page(
            request, course, student, notebook, message)

    try:
        action, _docker_name, actual_port, jupyter_token = completed_process.stdout.split()

        if action.startswith("failed"):
            message = ("failed to spawn notebook container\n"
                       "command {}\nreturned with retcod={} action={}\n"
                       "stdout:{}\n"
                       "stderr:{}").format(
                           " ".join(command), completed_process.returncode, action,
                           completed_process.stdout,
                           completed_process.stderr)
            return error_page(
                request, course, student, notebook, message)

        # remember that in events file for statistics
        Stats(course).record_open_notebook(student, notebook, action, actual_port)
        # redirect with same proto (http or https) as incoming
        scheme = request.scheme
        # get the host part of the incoming URL
        host = request.get_host()
        # remove initial port if present in URL
        if ':' in host:
            host, _ = host.split(':', 1)
        ########## forge a URL that nginx will intercept
        # port depends on scheme - we do not specify it
        # passing along course and student is for 'reset_from_origin'
        url = (f"{scheme}://{host}/{actual_port}/notebooks/"
               f"{notebook_withext}?token={jupyter_token}&"
               f"course={course}&student={student}")
        logger.info(f"edxfront: redirecting to {url}")
#        return HttpResponse('<a href="{}">click to be redirected</h1>'.format(url))
        return HttpResponseRedirect(url)

    except Exception as exc:
        message = (f"exception when parsing output of nbh {subcommand}\n"
                   f"{completed_process.stdout}\n"
                   f"{type(exc): exc}")
        # logger.exception(message)
        return error_page(
            request, course, student, notebook, message)


def share_notebook(request, course, student, notebook):
    """
    the URL to create static snapshots; it is intended to be fetched through ajax

    * computes a hash for storing the output
    * runs nbconvert in the student's container
    * stores the result in /nbhosting/snapshots/<course>/<hash>.html
    * returns a JSON-encoded dict that is either
      * { url: "/snapshots/flotpython/5465789765789.html" }
      * or { error: "the error message" }
    """

    # the ipynb extension is removed from the notebook name in urls.py
    notebook_withext = notebook + ".ipynb"
    # compute hash from the input, so that a second run on the same notebook
    # will override any previsouly published static snapshot
    hasher = hashlib.sha1(bytes('{}-{}-{}'.format(course, student, notebook),
                                encoding='utf-8'))
    hash = hasher.hexdigest()

    subcommand = 'docker-share-student-course-notebook-in-hash'

    command = ['nbh', '-d', sitesettings.nbhroot]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

    command += [student, course, notebook_withext, hash]

    logger.info(f"In {Path.cwd()}\n"
                f"-> Running command {' '.join(command)}")
    completed_process = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed_process, subcommand)

    if completed_process.returncode != 0:
        message = "command {} returned {}\nstderr:{}"\
                  .format(" ".join(command),
                          completed_process.returncode,
                          completed_process.stderr)
        return JsonResponse(dict(error=message))

    # expect docker-share-student-course-notebook
    # to write a url_path on its stdout
    url_path = completed_process.stdout.strip()
    logger.info(f"reading url_path={url_path}")
    # rebuild a full URL with proto and hostname,
    url = f"{request.scheme}://{request.get_host()}{url_path}"
    return JsonResponse(dict(url_path=url_path, url=url))

# pylint: disable=r0914
def jupyterdir_forward(request, course, student, jupyter_url):

    """
    this entry point is for opening a student's course directory
    using jupyter classic, allowing for regular navigation
    what it does is
    * check if the student already exists and has the course dir
    * make sure the student container is ready to answer http requests
    and then returns a http redirect to /port/<notebook_path>
    """

    logger.info(f"jupyterdir_forward: jupyter_url={jupyter_url}")
    logger.info(f"jupyterdir_forward: GET={request.GET}")
    all_right, explanation = authorized(request)

    if not all_right:
        return HttpResponseForbidden(
            f"Access denied: {explanation}")

    # minimal filtering
    allowed_verbs = (
        'tree',     # classic notebook
        'lab',      # jupyterlab
        'git-pull', # nbgitpuller
    )

    if not any(jupyter_url.startswith(verb) for verb in allowed_verbs):
        return HttpResponseForbidden(
            f"Access denied: verb not in {allowed_verbs} with {jupyter_url}")

    # nbh's subcommand
    subcommand = 'docker-view-student-course-jupyterdir'

    # build command
    command = ['nbh', '-d', sitesettings.nbhroot]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

    # add arguments to the subcommand
    command += [student, course]
    logger.info(f'In {Path.cwd()}\n-> Running command {" ".join(command)}')
    completed_process = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed_process, subcommand)

    if completed_process.returncode != 0:
        message = "command {} returned {}\nstderr:{}"\
                  .format(" ".join(command),
                          completed_process.returncode,
                          completed_process.stderr)
        return error_page(
            request, course, student, "jupyterdir", message)

    try:
        action, _docker_name, actual_port, jupyter_token = completed_process.stdout.split()

        if action.startswith("failed"):
            message = ("failed to spawn notebook container\n"
                       "command {}\nreturned with retcod={} action={}\n"
                       "stdout:{}\n"
                       "stderr:{}").format(
                           " ".join(command), completed_process.returncode, action,
                           completed_process.stdout,
                           completed_process.stderr)
            return error_page(
                request, course, student, "jupyterdir", message)

        # remember that in events file for statistics
        # not yet implemented on the Stats side
        # Stats(course).record_open_notebook(student, notebook, action, actual_port)
        # redirect with same proto (http or https) as incoming
        scheme = request.scheme
        # get the host part of the incoming URL
        host = request.get_host()
        # remove initial port if present in URL
        if ':' in host:
            host, _ = host.split(':', 1)
        ########## forge a URL that nginx will intercept
        # port depends on scheme - we do not specify it
        # passing along course and student is for 'reset_from_origin'
        url = (f"{scheme}://{host}/{actual_port}/{jupyter_url}"
               f"?token={jupyter_token}"
               f"&course={course}&student={student}")
        for k, v in request.GET.items():
            url += f"&{k}={v}"
        logger.info(f"jupyterdir_forward: redirecting to {url}")
        return HttpResponseRedirect(url)

    except Exception as exc:
        message = (f"exception when parsing output of nbh {subcommand}\n"
                   f"{completed_process.stdout}\n"
                   f"{type(exc): exc}")
        # logger.exception(message)
        return error_page(
            request, course, student, "jupyterdir", message)
