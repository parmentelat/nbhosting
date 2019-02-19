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

######### auditor

@login_required
@csrf_protect
def auditor_list_courses(request):
    courses_dir = CoursesDir()
    return render(request, "auditor-courses.html",
                  {'courses': courses_dir.coursenames()})


@login_required
@csrf_protect
def auditor_show_course(request, course, viewpoint):
    viewpoint = viewpoint or "course"
    course_dir = CourseDir(course)
    # xxx need a way to set viewpoint somewhere on the URL
    # like .e.g. 'exos'
    sections = course_dir.sections(viewpoint)
    for section in sections:
        for notebook in section.notebooks:
            notebook.in_course = True

    # read student dir
    read_notebook_paths = set(
        course_dir.probe_student_notebooks(request.user.username))

    # mark corresponding notebook instances as read
    for read_path in read_notebook_paths:
        for section in sections:
            spotted = section.spot_notebook(read_path)
            if spotted:
                spotted.in_student = True
                break
        # existing in the student tree, but not in the
        # course / viewpoint
        odd_notebook = Notebook(course_dir, read_path)
        odd_notebook.in_student = True
        sections.add_unknown(odd_notebook)


    env = dict(
        course=course,
        viewpoint=viewpoint,
        sections=sections,
        how_many=len(course_dir),
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
