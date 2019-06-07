# pylint: disable=c0111, w1203

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
def auditor_show_notebook(request, course, notebook=None, track=None):

    student = request.user.username

    # don't want to mess with the urls
    trackname = track
    coursedir = CourseDir(course)
    if trackname is None:
        trackname = coursedir.tracknames()[0]
    track = coursedir.track(trackname)
    track.mark_notebooks(student)

    if notebook is None:
        notebook_obj = track.sections[0].notebooks[0]
        notebook = notebook_obj.clean_path()
        print(f"default notebook -> {notebook}")
    else:
        notebook_obj = track.spot_notebook(notebook)

    # compute title as notebookname if found in sections
    title = notebook_obj.notebookname if notebook_obj else notebook
    giturl = coursedir.giturl
    iframe = f"/ipythonExercice/{course}/{notebook}/{student}"
    gitpull_url = (f"/ipythonForward/{course}/{student}/git-pull"
                   f"?repo={giturl}"
                   f"&autoRedirect=false"
                   f"&toplevel=."
                   f"&redirectUrl={iframe}"
                   )
    tracks = coursedir.tracks()

    return render(
        request, "auditor-notebook.html",
        dict(
            coursename=course,
            coursedir=coursedir,
            track=track,
            notebook=notebook,
            iframe=iframe,
            gitpull_url=gitpull_url,
            head_title=f"nbh:{course}",
            title=title,
            tracks=tracks,
            student=student,
        ))


######### staff

@staff_member_required
@csrf_protect
def staff_list_courses(request):
    courses_dir = CoursesDir()
    course_dirs = [
        CourseDir(name) for name in courses_dir.coursenames()
    ]
    return render(request, "staff-courses.html",
                  {'course_dirs': course_dirs})

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
