# pylint: disable=c0111, r1705

from pathlib import Path
import subprocess
import hashlib
import re

import pickle
import time
import itertools


from http import HTTPStatus
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden

from nbh_main.settings import sitesettings
from nbh_main.settings import logger, DEBUG
from nbhosting.courses.model_course import CourseDir, JLAB_NOTEBOOK_URL_FORMAT
from nbhosting.stats.stats import Stats

from nbhosting.version import __version__ as nbh_version
from nbh_main.settings import sitesettings

# Create your views here.

# use header=True when you have a short message
# and want to use is as the header too
def error_page(request, course, student, notebook, message,
               header="! nbhosting internal error !"):
    if header is True:
        header = message
    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        course=course, student=student,
        notebook=notebook, message=message, header=header)
    return render(request, "error.html", context=env,
                  status=HTTPStatus.BAD_REQUEST)


def log_completed_process(completed, subcommand):
    header = f"{10 * '='} {subcommand}"
    logger.info(f"{header} returned ==> {completed.returncode}")
    for field in ('stdout', 'stderr'):
        text = getattr(completed, field, 'undef')
        # nothing to show
        if not text:
            continue
        # implement policy for stderr
        if field == 'stderr':
            # config has requested to not log stderr at all
            if sitesettings.DEBUG_log_subprocess_stderr is None:
                continue
            # config requires stderr only for failed subprocesses
            if sitesettings.DEBUG_log_subprocess_stderr is False \
               and completed.returncode == 0:
                continue
        logger.info(f"{header} - {field}")
        logger.info(text)


def failed_command_message(command_str, completed, prefix=None):
    result = ""
    if prefix:
        result += f"{prefix}\n"
    result += (
        f"command {command_str}\n"
        f"returned {completed.returncode}\n"
        f"stdout:{completed.stdout}\n"
        f"stderr:{completed.stderr}")
    return result


def failed_command_header(action):
    if action == 'failed-garbage-collecting':
        return 'Please try again later'
    elif action == 'failed-stopped-container':
        return 'Unexpected stopped container'
    elif action == 'failed-cannot-retrieve-port':
        return 'Cannot retrieve port number'
    elif action == 'failed-timeout':
        return 'Your container is taking too long to answer'
    elif action == 'failed-unknown-image':
        return 'Image not found for course'
    else:
        # failed-cannot-add-student-in-course
        # failed-unknown-student $student
        # failed-cannot-add-student-in-course
        # failed-student-has-no-workdir
        return action


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
        explanation = f"HTTP_REFERER = {referer}, allowed_referer_domains = {domains}"
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
        explanation = (f"REMOTE_ADDR = {incoming_ip}, "
                       f"allowed_devel_ips = {allowed_devel_ips}")
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

    xxx possibly this could make simpler, especially with notebooks
    that only save themselves under a single format - as dual-format
    is a real pain in terms of updating a student's space
    most likely it should use sitesettings.notebook_extensions
    but it's safer to keep it that way until the bulk of 2019/2020
    courses is not over
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
    if suffix not in policies:
        return False, None, None, None
    variants = policies[suffix]
    for variant in variants:
        s = p.parent / p.stem
        c = p.parent / (p.stem + variant)
        if c.exists():
            return (True, str(c.relative_to(top)),
                    str(s.relative_to(top)),
                    # with jupytext in the picture,
                    # any .md file can be opened as a notebook
                    # variant != '.md'
                    True
                    )
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
            f"no such course `{coursename}'", header=True,
        )

    # the ipynb extension is removed from the notebook name in urls.py
    exists, notebook_with_ext, _, is_genuine_notebook = \
        locate_notebook(coursedir.git_dir, notebook)

    # second attempt from the student's space
    # in case the student has created it locally...
    if not exists:
        exists, notebook_with_ext, _, is_genuine_notebook = \
            locate_notebook(coursedir.student_dir(student), notebook)

    if not exists:
        msg = f"notebook `{notebook}' not known in this course or student"
        return error_page(request, coursename, student, notebook,
                          msg, header="notebook not found")


    # deal with concurrent requests on the same container
    # by using a shared memory (a redis cache)
    # starting_containers is the cache name
    # as configured in nbhosting.ini(.in)

    # in devel mode we don't have redis
    redis_cache = None
    try:

        import redis
        idling = 0.5
        # just a safety in case our code would not release stuff properly
        expire_in_s = 15

        def my_repr(timedelta):
            return f"{timedelta.seconds}s {timedelta.microseconds}µs"

        redis_cache = redis.Redis()
        container = f'{coursename}-x-{student}'
        for attempt in itertools.count(1):
            already = redis_cache.get(container)

            # good to go
            if not already:
                logger.info(f"{attempt=} going ahead with {container=} and {notebook=}")
                redis_cache.set(container, b'1')
                redis_cache.expire(container, expire_in_s)
                break

            # has the stored token expired ?
            logger.info(f"{attempt=} waiting for {idling=} because {container} is being started"
                        f"with {container=} and {notebook=}")
            time.sleep(idling)
    except ModuleNotFoundError:
        # make sure this error does not go unnoticed in production
        if not DEBUG:
            raise
        else:
            pass


    subcommand = 'container-view-student-course-notebook'

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

    # add arguments to the subcommand
    command += [student, coursename, notebook_with_ext,
                coursedir.image, ref_giturl]
    command_str = " ".join(command)
    logger.info(f'edxfront is running (DEBUG={DEBUG}): {command_str}')
    completed = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed, subcommand)

    try:
        action, _container_name, actual_port, jupyter_token = completed.stdout.split()

        if completed.returncode != 0 or action.startswith("failed"):
            message = failed_command_message(
                command_str, completed, prefix="failed to spawn notebook container")
            header = failed_command_header(action)
            return error_page(
                request, coursename, student, notebook, message, header)

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
        # passing along course and student is for 'reset_from_origin'
        if is_genuine_notebook:
            # make sure the settings are loaded
            coursedir.probe()
            notebook_url_format = coursedir.notebook_url_format
            path = notebook_url_format.format(notebook=notebook_with_ext)
            # url_format may already come with a '?'
            # in which case our additions must use '&'
            sep = '?' if '?' not in path else '&'
            url = (f"{scheme}://{host}/{actual_port}/{path}"
                   f"{sep}token={jupyter_token}"
                   f"&course={coursename}"
                   f"&student={student}")
        # otherwise enter jlab so that one can browse the contents
        else:
            path = JLAB_NOTEBOOK_URL_FORMAT.format(notebook=notebook_with_ext)
            url = (f"{scheme}://{host}/{actual_port}/{path}")
        logger.info(f"edxfront: redirecting to {url}")
        return HttpResponseRedirect(url)

    except Exception as exc:
        prefix = (f"exception when parsing output of nbh {subcommand}\n"
                   f"{type(exc)}: {exc}")
        message = failed_command_message(command_str, completed, prefix=prefix)
        return error_page(
            request, coursename, student, notebook, message)
    finally:
        if redis_cache:
            redis_cache.delete(container)


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

    coursedir = CourseDir.objects.get(coursename=course)
    student_dir = coursedir.student_dir(student)
    exists, with_ext, without_ext, is_notebook = locate_notebook(student_dir, notebook)
    if not exists or not is_notebook:
        message = f"cannot spot notebook {notebook}"
        return JsonResponse(dict(error=message))

    ext = with_ext.replace(without_ext, "")
#    debug = f"{with_ext=} {without_ext=} {ext=}"
#    logger.info(debug)

    # nbconvert works only from a .ipynb
    # invoke jupytext to produce that one
    if ext != '.ipynb':
        with_original_ext = with_ext
        with_ext = f"{without_ext}.ipynb"
        command_str = f"cd {student_dir}; jupytext --to ipynb -o {with_ext} {with_original_ext}"
        logger.info(f"In {Path.cwd()}\n"
                    f"-> Running command {command_str}")
        completed = subprocess.run(
            command_str, universal_newlines=True, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_completed_process(completed, 'jupytext')
        if completed.returncode != 0:
            message = failed_command_message(command_str, completed)
            return JsonResponse(dict(error=message))


    # compute hash from the input, so that a second run on the same notebook
    # will override any previsouly published static snapshot
    hasher = hashlib.sha1(bytes(f'{course}-{student}-{without_ext}',
                                encoding='utf-8'))
    hash = hasher.hexdigest()

    subcommand = 'container-share-student-course-notebook-in-hash'

    command = ['nbh', '-d', sitesettings.nbhroot]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

    command += [student, course, with_ext, hash]
    command_str = " ".join(command)

    logger.info(f"In {Path.cwd()}\n"
                f"-> Running command {' '.join(command)}")
    completed = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed, subcommand)

    if completed.returncode != 0:
        message = failed_command_message(command_str, completed)
        return JsonResponse(dict(error=message))

    # expect the subcommand to write a url_path on its stdout
    url_path = completed.stdout.strip()
    logger.info(f"reading url_path={url_path}")
    # rebuild a full URL with proto and hostname,
    url = f"{request.scheme}://{request.get_host()}{url_path}"
    return JsonResponse(dict(url_path=url_path, url=url))


# we must use course as an argument name because of the way urls.py works
# but it's clearer if we can use coursename as a parameter name, so....
def jupyterdir_forward(request, course, student, jupyter_url):

    """
    this entry point is for opening a student's course directory
    using jupyter classic, allowing for regular navigation
    what it does is
    * check if the student already exists and has the course dir
    * make sure the student container is ready to answer http requests
    and then returns a http redirect to /port/<notebook_path>
    """
    return _jupyterdir_forward(request, course, student, jupyter_url)

# pylint: disable=r0914
def _jupyterdir_forward(request, coursename, student, jupyter_url):

    logger.debug(f"jupyterdir_forward: {jupyter_url=}")
    logger.debug(f"jupyterdir_forward: {request.GET=}")
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

    coursedir = CourseDir.objects.get(coursename=coursename)
    if not coursedir.is_valid():
        return error_page(
            request, coursename, student, "n/a",
            f"no such coursename {coursename}"
        )

    # nbh's subcommand
    subcommand = 'container-view-student-course-jupyterdir'

    # build command
    command = ['nbh', '-d', sitesettings.nbhroot]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

    # add arguments to the subcommand
    command += [student, coursename, coursedir.image]
    command_str = " ".join(command)
    logger.info(f"Running command {command_str}")
    completed = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed, subcommand)

    if completed.returncode != 0:
        message = failed_command_message(command_str, completed)
        return error_page(
            request, coursename, student, "jupyterdir", message)

    try:
        action, _container_name, actual_port, jupyter_token = completed.stdout.split()

        if completed.returncode != 0 or action.startswith("failed"):
            message = failed_command_message(
                command_str, completed, prefix="failed to spawn notebook container")
            header = failed_command_header(action)
            return error_page(
                request, coursename, student, "n/a", message, header)

        # remember that in events file for statistics
        # not yet implemented on the Stats side
        # Stats(coursename).record_open_notebook(student, notebook, action, actual_port)
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
               f"&course={coursename}&student={student}")
        for k, v in request.GET.items():
            url += f"&{k}={v}"
        logger.info(f"jupyterdir_forward: redirecting to {url}")
        return HttpResponseRedirect(url)

    except Exception as exc:
        prefix = (f"exception when parsing output of nbh {subcommand}\n"
                   f"{type(exc)}: {exc}")
        message = failed_command_message(command_str, completed, prefix=prefix)
        return error_page(
            request, coursename, student, "jupyterdir", message)


def container_kill_request(request, course, student):
    # xxx the names in urls.py need a cleanup
    coursename = course
    logger.info(f"container_kill_request: {coursename} x {student}")
    all_right, explanation = authorized(request)

    if not all_right:
        return HttpResponseForbidden(
            f"Access denied: {explanation}")

    coursedir = CourseDir.objects.get(coursename=coursename)
    if not coursedir.is_valid():
        return error_page(
            request, coursename, student, "n/a",
            f"no such coursename {coursename}"
        )

    success = coursedir.kill_student_container(student)
    if not success:
        return error_page(
            request, coursename, student, "n/a", "could not kill container"
        )

    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        coursename=coursename, student=student)
    return render(request, "container-killed.html", env)
