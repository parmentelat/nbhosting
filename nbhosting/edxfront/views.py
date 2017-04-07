from pathlib import Path
import subprocess
import pprint

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from nbhosting.main.settings import logger, nbhosting_settings as settings
from nbhosting.stats.stats import Stats

# Create your views here.

def error_page(course, student, notebook, message=None):
    html = ""
    html += "<h1>nbhosting internal error</h1>"
    html += "<p>"
    html += "Error for course {} with student {}"\
            .format(course, student)
    html += "<br/>"
    html += "Notebook was {}".format(notebook)
    if message:
        html += "<br/>"
        html += message
    html += "</p>"
    return HttpResponse(html)

def verbatim(text):
    return "<pre><code>{}</code></pre>".format(text)

def log_completed_process(cp):
    for field in ('returncode', 'stdout', 'stderr'):
        logger.info("proc returned <- {}={}"
                    .format(field, pprint.pformat(getattr(cp, field, 'undef'))))

# the main edxfront entry point
def edx_request(request, course, student, notebook):

    root = settings['root']
    # the ipynb extension is removed from the notebook name in urls.py
    notebook_full = notebook + ".ipynb"
    
    # xxx probably requires a sudo of some kind here
    # for when run from apache or nginx or whatever

    script = 'nbh-enroll-student-in-course'
    command = [ script, root, student, course ]
    logger.info("In {}\n-> Running command {}".format(Path.cwd(), " ".join(command)))
    completed_process = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed_process)

    script = 'nbh-run-student-course-jupyter'
    # use image named after the course for now
    image = course
    command = [ script, root, student, course, notebook_full, image ]
    logger.info("In {}\n-> Running command {}".format(Path.cwd(), " ".join(command)))
    completed_process = subprocess.run(
        command, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log_completed_process(completed_process)

    if completed_process.returncode != 0:
        return error_page(
            course, student, notebook,
            "command {} returned {}<br/>stderr:{}"
            .format(" ".join(command), completed_process.returncode,
                    verbatim(completed_process.stderr)))
    try:
        action, docker_name, actual_port, jupyter_token = completed_process.stdout.split()
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
        # do not specify a port, it will depend on the scheme
        # and probably be https/443
        url = "{scheme}://{host}/{port}/notebooks/{path}?token={token}"\
              .format(scheme=scheme, host=host, port=actual_port,
                      path=notebook_full, token=jupyter_token)
        logger.info("edxfront: redirecting to {}".format(url))
#        return HttpResponse('<a href="{}">click to be redirected</h1>'.format(url))
        return HttpResponseRedirect(url)           

    except Exception as e:
        return error_page(
            course, student, notebook,
            "exception when parsing output of {}<br/>{}<br/>{}"
            .format(script, verbatim(completed_process.stdout), verbatim(e)))
