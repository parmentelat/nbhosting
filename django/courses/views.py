import os.path
import subprocess

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbhosting.settings import nbhosting_settings

# Create your views here.

def stdout_html(message, stdout):
    html = ""
    if stdout:
        html += "<p class='stdout'>OUTPUT {message}</p>".format(message=message)
        html += "<pre>\n{stdout}</pre>".format(stdout=stdout)
    return html

def stderr_html(message, stderr):
    html = ""
    if stderr:
        html += "<p class='stderr'>ERROR {message}</p>".format(message=message)
        html += "<pre>\n{stderr}</pre>".format(stderr=stderr)
    return html

#def stderr_page(message, stderr):
#    return HttpResponse(stderr_page(message, stderr))

def top_link(html):
    return "<a class='top-link' href='/nbh/'>{html}</a>".format(html=html)

@login_required
@csrf_protect
def list_courses(request):
    root = nbhosting_settings['root']
    courses_git_dir = os.path.join(root, "courses-git")
    command = [ "ls", courses_git_dir ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        return render(request, "error.html", {
            'message' : "when listing courses",
            'stderr'  :  completed.stderr})
    return render(request, "courses.html",
                  {'courses' : [ c for c in completed.stdout.decode().split("\n") if c ]})


@login_required
@csrf_protect
def list_course(request, course):
    root = nbhosting_settings['root']
    course_root = os.path.join(root, "courses", course)
    command = [ "find", course_root, "-name", "*.ipynb"]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        return render(request, "error.html", {
            'message' : "when listing notebooks in {course}".format(course=course),
            'stderr'  :  completed.stderr})
    def normalize(path):
        path = path.replace(course_root, "")
        if path.startswith('/'):
            path = path[1:]
        if path.endswith(".ipynb"):
            path = path[:-6]
        return path
    notebooks = [
        normalize(path) for path in completed.stdout.decode().split("\n")
        if path and 'ipynb_checkpoints' not in path]

    return render(request, "course.html", {
        'course' : course,
        'notebooks': notebooks })

@login_required
@csrf_protect
def update_course(request, course):
    root = nbhosting_settings['root']
    command = [ "nbh-update-course", root, course]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        return render(request, "error.html", {
            'message' : "when updating {course}".format(course=course),
            'stderr'  :  completed.stderr})

    return render(request, "course-updated.html",
                  { 'course' : course,
                    'stdout' : completed.stdout,
                    'stderr' : completed.stderr,
                    'returncode' : completed.returncode})
