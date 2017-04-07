from pathlib import Path
import subprocess

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbhosting.main.settings import nbhosting_settings
from nbhosting.courses.models import CoursesDir, CourseDir

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


@login_required
@csrf_protect
def list_courses(request):
    courses_dir = CoursesDir()
    return render(request, "courses.html",
                  {'courses' : courses_dir.coursenames})

@login_required
@csrf_protect
def list_course(request, course):
    course_dir = CourseDir(course)
    notebooks = course_dir.notebooks()
    
    return render(request, "course.html", {
        'how_many' : len(notebooks),
        'course' : course,
        'notebooks': notebooks })

@login_required
@csrf_protect
def update_course(request, course):
    course_dir = CourseDir(course)
    completed = course_dir.update_completed()
    command = " ".join(completed.args)
    message = "when updating {course}".format(course=course)
    # expose most locals, + the attributes of completed
    # like stdout and stderr
    env = vars(completed)
    env.update(locals())
    # this is an instance and so would not serialize
    del env['course_dir']
    template = "course-updated.html"
    return render(request, template, env)
