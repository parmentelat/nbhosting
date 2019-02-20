# we keep on exposing local variables to a template
# using locals(); hence disable w0641 - unused variable
# pylint: disable=c0111, w0641
#from pathlib import Path
#import subprocess

from django.shortcuts import render
#from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from nbhosting.courses import CoursesDir, CourseDir, Notebook
from nbhosting.main.settings import logger

######### auditor

@login_required
@csrf_protect
def auditor_list_courses(request):
    courses_dir = CoursesDir()
    return render(request, "auditor-courses.html",
                  {'courses': courses_dir.coursenames()})


@login_required
@csrf_protect
def auditor_show_course(request, course, track=None):
    track = track or "course"
    coursedir = CourseDir(course)
    sections = coursedir.sections(track)
    student = request.user.username
    sections.mark_notebooks(student)

    notebook = sections[0].notebooks[0]
    logger.debug(f"after mark {notebook.__dict__}")
    logger.debug(f"classes => {notebook.classes()}")

    env = dict(
        course=course,
        track=track,
        sections=sections,
        how_many=len(coursedir),
    )
    return render(request, "auditor-course.html", env)


@login_required
@csrf_protect
def auditor_show_notebook(request, course, notebook, track=None):
    student = request.user.username
    course_track = course if not track else f"{course}:{track}"
    track = track if track is not None else "course"
    coursedir = CourseDir(course)
    sections = coursedir.sections(track)
    sections.mark_notebooks(request.user.username)
    return render(
        request, "auditor-notebook.html",
        dict(
            course=course,
            track=track,
            sections=sections,
            notebook=notebook,
            iframe=f"/ipythonExercice/{course}/{notebook}/{student}",
            course_track=course_track,
            head_title=f"{course}",
        ))


######### staff

@staff_member_required
@csrf_protect
def staff_list_courses(request):
    courses_dir = CoursesDir()
    course_details = [
        dict(name=name,
             homedirs=CourseDir(name).student_homes())
        for name in courses_dir.coursenames()
        ]
    return render(request, "staff-courses.html",
                  {'course_details': course_details})

@staff_member_required
@csrf_protect
def staff_show_course(request, course):
    coursedir = CourseDir(course)
    notebooks = list(coursedir.notebooks())
    notebooks.sort()
    # shorten staff hashes

    shorten_staff = [hash[:7] for hash in coursedir.staff]

    env = dict(
        course=course,
        notebooks=notebooks,
        how_many=len(notebooks),
        image=coursedir.image,
        statics=coursedir.statics,
        staff=shorten_staff,
        giturl=coursedir.giturl,
    )
    return render(request, "staff-course.html", env)


def nbh_manage(request, course, verb, _managed):
    coursedir = CourseDir(course)
    if verb == 'update-from-git':
        completed = coursedir.update_from_git()
    elif verb == 'build-image':
        completed = coursedir.build_image()
    elif verb == 'clear-staff':
        completed = coursedir.clear_staff()
    command = " ".join(completed.args)
    message = "when updating {course}".format(course=course)
    # expose most locals, + the attributes of completed
    # like stdout and stderr
    env = vars(completed)
    env.update(locals())
    # this is an instance and so would not serialize
    del env['coursedir']
    # the html title
    template = "course-managed.html"
    return render(request, template, env)


@staff_member_required
@csrf_protect
def update_from_git(request, course):
    return nbh_manage(request, course, 'update-from-git', 'updated')


@staff_member_required
@csrf_protect
def build_image(request, course):
    return nbh_manage(request, course, 'build-image', 'rebuilt')


@staff_member_required
@csrf_protect
def clear_staff(request, course):
    return nbh_manage(request, course, 'clear-staff', 'staff cleared')
