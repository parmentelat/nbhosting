import os
import os.path
import subprocess

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from nbhosting.settings import nbhosting_settings as settings

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

# the main frontend entry point
# the ipynb extension is removed from the notebook name in urls.py
def notebook_request(request, course, student, notebook):

    root = settings['root']
    # xxx probably requires a sudo of some kind here
    # for when run from apache or nginx or whatever

    script = os.path.join(root, 'scripts/add-student-in-course')
    command = [ script, root, student, course ]
    print("pwd={}".format(os.getcwd()))
    print("Running command", " ".join(command))
    completed_process = subprocess.run(command,
                                       universal_newlines=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    print(completed_process)

    script = os.path.join(root, 'scripts/run-student-course-jupyter')

    notebook_full = notebook + ".ipynb"
    command = [ script, root, student, course, notebook_full ]
    print("Running command", " ".join(command))
    completed_process = subprocess.run(command,
                                       universal_newlines=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

    if completed_process.returncode != 0:
        print(completed_process)
        return error_page(
            course, student, notebook,
            "command {} returned {}<br/>stderr:{}"
            .format(command, completed_process.returncode,
                    verbatim(completed_process.stderr)))
    try:
        docker_name, docker_port, jupyter_token = completed_process.stdout.split()
        host = request.get_host()
        url = "http://{}:{}/notebooks/{}?token={}"\
              .format(host, docker_port, notebook_full, jupyter_token)
        print("host={} new port = {}".format(host, docker_port))
        print("redirecting to {}".format(url))
        return HttpResponseRedirect(url)

    except Exception as e:
        return error_page(
            course, student, notebook,
            "exception when parsing output of {}<br/>{}"
            .format(script, verbatim(e)))
    
