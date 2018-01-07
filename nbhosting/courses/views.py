from pathlib import Path
import subprocess

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbhosting.courses.models import CoursesDir, CourseDir

# Create your views here.


def stdout_html(message, stdout):
    html = ""
    if stdout:
        html += "<p class='stdout'>OUTPUT {message}</p>".format(
            message=message)
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
                  {'courses': courses_dir.coursenames()})


@login_required
@csrf_protect
def list_course(request, course):
    course_dir = CourseDir(course)
    notebooks = course_dir.notebooks()
    notebook_cols = [
        notebooks[::2],
        notebooks[1::2],
    ]

    # shorten staff hashes

    shorten_staff = [hash[:7] for hash in course_dir.staff]

    env = {
        'how_many': len(notebooks),        
        'image': course_dir.image,
        'statics': course_dir.statics,
        'staff': shorten_staff,
        'giturl': course_dir.giturl,
    }
    env.update(locals())
    return render(request, "course.html", env)


def nbh_manage(request, course, verb, managed):
    course_dir = CourseDir(course)
    if verb == 'update-from-git':
        completed = course_dir.update_from_git()
    elif verb == 'build-image':
        completed = course_dir.build_image()
    elif verb == 'clear-staff':
        completed = course_dir.clear_staff()
    command = " ".join(completed.args)
    message = "when updating {course}".format(course=course)
    # expose most locals, + the attributes of completed
    # like stdout and stderr
    env = vars(completed)
    env.update(locals())
    # this is an instance and so would not serialize
    del env['course_dir']
    # the html title
    template = "course-managed.html"
    return render(request, template, env)
        
        
@login_required
@csrf_protect
def update_from_git(request, course):
    return nbh_manage(request, course, 'update-from-git', 'updated')


@login_required
@csrf_protect
def build_image(request, course):
    return nbh_manage(request, course, 'build-image', 'rebuilt')


@login_required
@csrf_protect
def clear_staff(request, course):
    return nbh_manage(request, course, 'clear-staff', 'staff cleared')
