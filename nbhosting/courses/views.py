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
    course_dirs = [
        CourseDir(coursename) for coursename in courses_dir.coursenames()]
    return render(request, "auditor-courses.html",
        dict(course_dirs = course_dirs))


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
        course=course,
        tracks=tracks,
        track=track,
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
            course=course,
            coursedir=coursedir,
            track=track,
            notebook=notebook,
            iframe=f"/ipythonExercice/{course}/{notebook}/{student}",
            head_title=f"nbh:{course}",
            title=title,
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
        static_mappings=coursedir.static_mappings,
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
    elif verb == 'show-tracks':
        completed = coursedir.show_tracks()
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

@staff_member_required
@csrf_protect
def show_tracks(request, course):
    return nbh_manage(request, course, 'show-tracks', 'tracks recomputed')
