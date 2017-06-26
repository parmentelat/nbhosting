from pathlib import Path
import subprocess
import pprint

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

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

# the main edxfront entry point
def edx_request(request, course, student, notebook):

    root = settings['root']
    # the ipynb extension is removed from the notebook name in urls.py
    notebook_withext = notebook + ".ipynb"
    
    # xxx probably requires a sudo of some kind here
    # for when run from apache or nginx or whatever

    # using docker
    subcommand = 'docker-view-student-course-notebook'
    # build command
    command = ['nbh', '-d', root]
    if DEBUG:
        command.append('-x')
    command.append(subcommand)

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
        # do not specify a port, it will depend on the scheme
        # and probably be https/443
        url = "{scheme}://{host}/{port}/notebooks/{path}?token={token}"\
              .format(scheme=scheme, host=host, port=actual_port,
                      path=notebook_withext, token=jupyter_token)
        logger.info("edxfront: redirecting to {}".format(url))
#        return HttpResponse('<a href="{}">click to be redirected</h1>'.format(url))
        return HttpResponseRedirect(url)           

    except Exception as e:
        message = "exception when parsing output of nbh {}\n{}\n{}"\
                  .format(subcommand, completed_process.stdout, e)
        return error_page(
            request, course, student, notebook, message)
