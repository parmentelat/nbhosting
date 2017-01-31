import os.path
import subprocess

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect

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

def stderr_page(message, stderr):
    return HttpResponse(stderr_page(message, stderr))

def top_link(html):
    return "<a class='top-link' href='/nbh/'>{html}</a>".format(html=html)

@csrf_protect
def list_courses(request):
    root = nbhosting_settings['root']
    courses_git_dir = os.path.join(root, "courses-git")
    command = [ "ls", courses_git_dir ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        print(completed)
        return stderr_page("when listing courses", completed.stderr)
    html = ""
    html += top_link("<h1>Known courses</h1></a>")
    html += "<ul>"
    for course in completed.stdout.decode().split("\n"):
        if course:
            html += "<li class='course-link'><a href='/nbh/course/{course}'>{course}</a></li>"\
                                .format(course=course)
        
    html += "</ul>"
    return HttpResponse(html)

@csrf_protect
def list_course(request, course):
    root = nbhosting_settings['root']
    course_root = os.path.join(root, "courses", course)
    command = [ "find", course_root, "-name", "*.ipynb"]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    html = ""
    html += top_link("<h1>Course {course}</h1>".format(course=course))
    if completed.returncode != 0:
        print(completed)
        html += stderr_html("when listing notebooks in {course}"
                            .format(course=course),
                            completed.stderr)
    def student_link(notebook):
        if notebook.startswith('/'):
            notebook = notebook[1:]
        if notebook.endswith(".ipynb"):
            notebook = notebook[:-6]
        return "<a href='/ipythonExercice/{course}/{notebook}/anonymous'>{notebook}</a>"\
            .format(notebook=notebook, course=course)

    html += "<ul>"
    for path in completed.stdout.decode().split("\n"):
        if path and 'ipynb_checkpoints' not in path:
            notebook = path.replace(course_root, "")
            html += "<li>{link}</li>".format(link=student_link(notebook))
    html += "</ul>"
    ##########
    html += "<div class='update-course'><a href='/nbh/courses/update/{course}'>"\
            "Update {course}</a></div>".format(course=course)
    return HttpResponse(html)

@csrf_protect
def update_course(request, course):
    root = nbhosting_settings['root']
    command = [ "nbh-update-course", root, course]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    html = ""

    html += top_link("<h1>Updated course {}</h1>".format(course))

    html += stdout_html("when updating {course}".format(course=course),
                       completed.stdout)
    html += stderr_html("when updating {course}".format(course=course),
                       completed.stderr)
    html += "<p>Return code {}</p>"\
            .format("OK" if completed.returncode == 0 else returncode)
    redirect = "/nbh/course/{course}".format(course=course)
    html += "<a href='{redirect}'>Back to course {course}</a>"\
                      .format(redirect=redirect, course=course)
    return HttpResponse(html)
