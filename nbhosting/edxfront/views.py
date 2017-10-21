from pathlib import Path
import subprocess
import pprint
import hashlib
import re

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden

from nbhosting.main.settings import nbhosting_settings as settings
from nbhosting.main.settings import logger, DEBUG
from nbhosting.stats.stats import Stats

# Create your views here.


def error_page(request, course, student, notebook, message=None):
    env = locals()
    return render(request, "error.html", locals())


def log_completed_process(cp, subcommand):
    header = "{} {}".format(10 * '=', subcommand)
    logger.info("{} returned ==> {}".format(header, cp.returncode))
    for field in ('stdout', 'stderr'):
        text = getattr(cp, field, 'undef')
        if text:
            logger.info("{} - {}".format(header, field))
            logger.info(text)


# auth scheme here depends on the presence of META.HTTP_REFERER
# if present, check that one of the fields in 'allowed_referer_domains' appears in referer
# otherwise, performs check of META.REMOTE_ADDR against 'allowed_devel_ips'
def authorized(request):

    explanation = ""
    # check HTTP_REFERER against allowed_referer_domains
    def authorize_refered_request(request):
        # actual referer
        referer = request.META['HTTP_REFERER']
        domains = settings['allowed_referer_domains']
        result = any(domain in referer
                     for domain in domains)
        explanation = "HTTP_REFERER = {}, allowed_referer_domains = {}"\
                      .format(referer, domains)
        return result, explanation

    # check REMOTE_ADDR against allowed_devel_ips
    def authorize_devel_request(request):
        incoming_ip = request.META['REMOTE_ADDR']
        allowed_devel_ips = settings['allowed_devel_ips']
        result = False
        for mode, allowed in allowed_devel_ips:
            if mode == 'exact' and incoming_ip == allowed:
                result = True
            if mode == 'match' and re.match(allowed, incoming_ip):
                result = True
        explanation = "REMOTE_ADDR = {}, allowed_devel_ips = {}"\
                      .format(incoming_ip, allowed_devel_ips)
        return result, explanation
    
    # inside an iframe ?
    if 'HTTP_REFERER' in request.META:
        result, explanation = authorize_refered_request(request)
    else:
        result, explanation = authorize_devel_request(request)
    if not result:
        logger.warn("ACCESS REFUSED - check your nbhosting_settings"
                    "explanation = {}".format(explanation))
    return result

def edx_request(request, course, student, notebook):

    """
    the main edxfront entry point; it
    * creates a student if needed
    * copies the notebook if needed
    * makes sure the student container is ready to answer http requests
    and then returns a http redirect to /port/<notebook_path>
    """

    if not authorized(request):
        return HttpResponseForbidden()
    
    # the ipynb extension is removed from the notebook name in urls.py
    notebook_withext = notebook + ".ipynb"
    # have we received a request to force the copy (for reset_from_origin)
    forcecopy = request.GET.get('forcecopy', False)

    subcommand = 'docker-view-student-course-notebook'
    
    # build command
    command = ['nbh', '-d', settings['root']]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)
    # propagate the forcecopy flag for reset_from_origin
    if forcecopy:
        command.append('-f')

    # add arguments to the subcommand
    command += [ student, course, notebook_withext ]
    logger.info("In {}\n-> Running command {}".format(Path.cwd(), " ".join(command)))
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
        action, docker_name, actual_port, jupyter_token = completed_process.stdout.split()

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
        url = "{scheme}://{host}/{port}/notebooks/{path}?token={token}&course={course}&student={student}"\
              .format(scheme=scheme, host=host, port=actual_port,
                      path=notebook_withext, token=jupyter_token,
                      course=course, student=student)
        logger.info("edxfront: redirecting to {}".format(url))
#        return HttpResponse('<a href="{}">click to be redirected</h1>'.format(url))
        return HttpResponseRedirect(url)           

    except Exception as e:
        message = "exception when parsing output of nbh {}\n{}\n{}"\
                  .format(subcommand, completed_process.stdout, e)
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

    command = ['nbh', '-d', settings['root']]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

    command += [ student, course, notebook_withext, hash]

    logger.info("In {}\n-> Running command {}".format(Path.cwd(), " ".join(command)))
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

    # expect docker-share-student-course-notebook to write a url_path on its stdout
    url_path = completed_process.stdout.strip()
    logger.info("reading url_path={}".format(url_path))
    # rebuild a full URL with proto and hostname,
    url = "{scheme}://{hostname}{path}"\
          .format(scheme=request.scheme, hostname=request.get_host(), path=url_path)
    return JsonResponse(dict(url_path=url_path, url=url))
