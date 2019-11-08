# pylint: disable=c0111, r1705, w1203

from pathlib import Path
import subprocess
import hashlib
import re

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden

from nbh_main.settings import sitesettings
from nbh_main.settings import logger, DEBUG
from nbhosting.courses.model_course import CourseDir
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

def edx_request(request, course, student, notebook):
    """
    the main edxfront entry point; it
    * creates a student if needed
    * copies the notebook if needed
    * makes sure the student container is ready to answer http requests
    and then returns a http redirect to /port/<notebook_path>
    """
    # have we received a request to force the copy (for reset_from_origin)
    forcecopy = request.GET.get('forcecopy', False)

    return _open_notebook(request, course, student, notebook,
                          forcecopy=forcecopy, init_student_git=False)


def classroom_request(request, course, student, notebook):
    """
    same as above, but with another copying policy

    instead of copying notebooks on a need-by-need basis,
    the student's workspace gets initialized as a standalone git repo
    """

    return _open_notebook(request, course, student, notebook,
                          forcecopy=False, init_student_git=True)


def locate_notebook(directory, notebook):
    """
    with jupytext in the picture, and with our needs
    to be able to publish raw .md files, there is a need to 
    be a little smarter and to locate an actual contents 
    from the 'notebook' path
    
    returns a 4-uple
        exists notebook_with_extension notebook_without_extension is_notebook
    
    if exists is False, then all the rest is None
    otherwise
      directory/notebook_with_extension is an existing file
      
    policy according to notebook's suffix
    * if notebook ends up with .md
      it is assumed to be existing
    * if notebook does not end with anything
      search for .py then .ipynb then .md
    * if notebook ends in .ipynb
      search for .ipynb then .py
    * if notebook ends in .py
      search for .py and then .ipynb
    """
    logger.info(f"locate_notebook with {directory} and {notebook}")
    policies = {
        '.md' : ['.md'],
        '': ['.py', '.ipynb', '.md'],
        '.ipynb': ['.ipynb', '.py'],
        '.py': ['.py', '.ipynb'],
    }
    top = Path(directory)
    p = top / notebook
    suffix = p.suffix
    stem = p.stem
    if suffix not in policies:
        return False, None, None, None
    variants = policies[suffix]
    for variant in variants:
        s = p.parent / p.stem
        c = p.parent / (p.stem + variant)
        if c.exists():
            return (True, str(c.relative_to(top)), 
                    str(s.relative_to(top)), 
                    variant != '.md')
    return False, None, None, None
    

def _open_notebook(request, coursename, student, notebook,
                   *, forcecopy, init_student_git): # pylint: disable=r0914
    """
    implement both edx_request and classroom_request
    that behave almost exactly the same
    """
    ok, explanation = authorized(request)

    if not ok:
        return HttpResponseForbidden(
            f"Access denied: {explanation}")

    coursedir = CourseDir.objects.get(coursename=coursename)
    if not coursedir.is_valid():
        return error_page(
            request, coursename, student, notebook,
            f"no such course {coursename}"
        )

    # the ipynb extension is removed from the notebook name in urls.py
    exists, notebook_with_ext, notebook_without_ext, is_genuine_notebook = \
        locate_notebook(coursedir.git_dir, notebook)

    # second attempt from the student's space
    # in case the student has created it locally...
    if not exists:
        exists, notebook_with_ext, notebook_without_ext, is_genuine_notebook = \
            locate_notebook(coursedir.student_dir(student), notebook)
            
    if not exists:
        msg = f"notebook {notebook} not known in this course or student"
        return error_page(request, coursename, student, msg)

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
        # a student repo gets cloned from local course git
        # for lower delays when updating, and removing issues
        # like accessing private repos from the students space
        ref_giturl = str(coursedir.git_dir)
    else:
        ref_giturl = coursedir.giturl

    logger.info(f"DEBUGGING image={coursedir.image} and giturl={ref_giturl}")

    # add arguments to the subcommand
    command += [student, coursename, notebook_with_ext,
                coursedir.image, ref_giturl]
    logger.info(f'edxfront is running: {" ".join(command)}')
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
            request, coursename, student, notebook, message)

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
                request, coursename, student, notebook, message)

        # remember that in events file for statistics
        Stats(coursename).record_open_notebook(student, notebook, action, actual_port)
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
        if is_genuine_notebook:
            url = (f"{scheme}://{host}/{actual_port}/notebooks/"
                   f"{notebook_with_ext}?token={jupyter_token}&"
                   f"course={coursename}&student={student}")
        else:
            url = (f"{scheme}://{host}/{actual_port}/lab/tree/{notebook_with_ext}")
        logger.info(f"edxfront: redirecting to {url}")
#        return HttpResponse('<a href="{}">click to be redirected</h1>'.format(url))
        return HttpResponseRedirect(url)

    except Exception as exc:
        message = (f"exception when parsing output of nbh {subcommand}\n"
                   f"{completed_process.stdout}\n"
                   f"{type(exc)}: {exc}")
        # logger.exception(message)
        return error_page(
            request, coursename, student, notebook, message)


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
    notebook_with_ext = notebook + ".ipynb"
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

    command += [student, course, notebook_with_ext, hash]

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
