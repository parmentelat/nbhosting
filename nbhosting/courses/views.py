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

from nbhosting.courses import CoursesDir, CourseDir


######### auditor

@login_required
@csrf_protect
def auditor_list_courses(request):
    courses_dir = CoursesDir()
    return render(request, "auditor-courses.html",
                  {'courses': courses_dir.coursenames()})


@login_required
@csrf_protect
def auditor_show_course(request, course):
    course_dir = CourseDir(course)
    course_notebooks = set(course_dir.notebooks())
    read_notebooks = set(
        course_dir.probe_student_notebooks(request.user.username))

    all_notebooks = course_notebooks | read_notebooks

    notebook_details = [
        dict(path=notebook,
             in_course=(notebook in course_notebooks),
             in_student=(notebook in read_notebooks))
        for notebook in all_notebooks
    ]

    notebook_details.sort(
        key=lambda d: d['path']
    )

    env = dict(
        course=course,
        notebook_details=notebook_details,
        how_many=len(notebook_details),
    )
    return render(request, "auditor-course.html", env)


@login_required
@csrf_protect
def auditor_show_notebook(request, course, notebook, student):
    return render(
        request, "auditor-notebook.html",
        dict(
            course=course,
            notebook=notebook,
            iframe=f"/ipythonExercice/{course}/{notebook}/{student}",
            course_url=f"/auditor/course/{course}",
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
    course_dir = CourseDir(course)
    notebooks = list(course_dir.notebooks())
    notebooks.sort()
    # shorten staff hashes

    shorten_staff = [hash[:7] for hash in course_dir.staff]

    env = dict(
        course=course,
        notebooks=notebooks,
        how_many=len(notebooks),
        image=course_dir.image,
        statics=course_dir.statics,
        staff=shorten_staff,
        giturl=course_dir.giturl,
    )
    return render(request, "staff-course.html", env)


def nbh_manage(request, course, verb, _managed):
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
