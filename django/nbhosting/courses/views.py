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
from nbh_main.settings import logger

######### auditor

@login_required
@csrf_protect
def auditor_list_courses(request):
    courses_dir = CoursesDir()
    course_dirs = [
        CourseDir(coursename) for coursename in courses_dir.coursenames()]
    return render(request, "auditor-courses.html",
        dict(course_dirs=course_dirs))


@login_required
@csrf_protect
def auditor_show_course(request, course, track=None):
    # don't want to mess with the urls
    trackname = track
    coursedir = CourseDir(course)
    tracks = coursedir.tracks()
    if trackname is None:
        trackname = coursedir.tracknames()[0]
    track = coursedir.track(trackname)
    student = request.user.username
    track.mark_notebooks(student)

    env = dict(
        coursedir=coursedir,
        coursename=course,
        tracks=tracks,
        track=track,
        main_trackname=tracks[0].name,
    )
    return render(request, "auditor-course.html", env)


@login_required
@csrf_protect
def auditor_show_notebook(request, course, notebook, track=None):
    # don't want to mess with the urls
    trackname = track
    coursedir = CourseDir(course)
    if trackname is None:
        trackname = coursedir.tracknames()[0]
    track = coursedir.track(trackname)
    student = request.user.username
    track.mark_notebooks(student)
    # compute title as notebookname if found in sections
    notebook_obj = track.spot_notebook(notebook)
    title = notebook_obj.notebookname if notebook_obj else notebook
    return render(
        request, "auditor-notebook.html",
        dict(
            coursename=course,
            coursedir=coursedir,
            track=track,
            notebook=notebook,
            iframe=f"/ipythonExercice/{course}/{notebook}/{student}",
            head_title=f"nbh:{course}",
            title=title,
        ))


@login_required
@csrf_protect
def auditor_jupyterdir(request, course, lab=False):
    logger.info(f"auditor_jupyterdir {course}")

    coursedir = CourseDir(course)
    tracks = coursedir.tracks()
    student = request.user.username
    iframe = f"/ipythonBrowse/{course}/{student}"
    if lab:
        iframe += "/lab"
    return render(
        request, "auditor-jupyterdir.html",
        dict(
            coursename=course,
            coursedir=coursedir,
            tracks=tracks,
            iframe=iframe,
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
        coursedir=coursedir,
        coursename=course,
        notebooks=notebooks,
        how_many=len(notebooks),
        image=coursedir.image,
        static_mappings=coursedir.static_mappings,
        staff=shorten_staff,
        giturl=coursedir.giturl,
        tracks=coursedir.tracks(),
    )
    return render(request, "staff-course.html", env)


def render_subprocess_result(request, course,
                             subcommand, message, python, *args):
    """    triggers a subprocess and displays results
    in a web page with returncode, stdout, stderr

    this can be either a call to
    * plain nbh (for code written in bash) with managed=False
    * or to nbh-manage for code written in python

    """
    coursedir = CourseDir(course)
    completed = coursedir.nbh_subprocess(subcommand, python, *args)
    command = " ".join(completed.args)
    # expose most locals, + the attributes of completed
    # like stdout and stderr
    env = dict(
        course=course,
        message=message,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    # the html title
    template = "course-managed.html"
    return render(request, template, env)


@staff_member_required
@csrf_protect
def update_from_git(request, course):
    return render_subprocess_result(
        request, course,
        "course-update-from-git", 'updated', False)


@staff_member_required
@csrf_protect
def build_image(request, course):
    return render_subprocess_result(
        request, course,
        "course-build-image", 'rebuilt', True)


@staff_member_required
@csrf_protect
def clear_staff(request, course):
    return render_subprocess_result(
        request, course,
        "course-clear-staff", 'staff files cleared', False)


@staff_member_required
@csrf_protect
def show_tracks(request, course):
    return render_subprocess_result(
        request, course,
        "course-show-tracks", 'tracks recomputed', True)


@staff_member_required
@csrf_protect
def destroy_my_container(request, course):
    print("in view destroy_my_container")
    return render_subprocess_result(
        request, course,
        "course-destroy-student-container", "my container destroyed",
        True, request.user.username)
