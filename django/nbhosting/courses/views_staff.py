# pylint: disable=c0111, w1203, r1705

import json


from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required

from nbh_main.settings import NBHROOT
# from nbh_main.settings import logger

from nbhosting.courses.model_course import CourseDir
from nbhosting.courses.forms import UpdateCourseForm

from nbhosting.version import __version__ as nbh_version
from nbh_main.settings import sitesettings


######### staff

@staff_member_required
@csrf_protect
def staff_list_courses(request):
    course_dirs = CourseDir.objects.order_by('coursename')
    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        course_dirs=course_dirs,
    )
    return render(request, "staff-courses.html", env)

@staff_member_required
@csrf_protect
def staff_show_course(request, course):
    coursedir = CourseDir.objects.get(coursename=course)
    #print(f"in staff_show_course: {hasattr(coursedir, 'image')}")
    coursedir.probe()
    notebooks = list(coursedir.notebooks())
    notebooks.sort()

    def enriched_group(group):
        def student_struct(user):
            return {
                'display': user.username,
                'id': user.id,
                'tooltip': user.username
                             if not user.first_name and not user.last_name
                             else f"{user.first_name} {user.last_name}",
            }

        result = {}
        result['group'] = group
        result['name'] = group.name
        result['number_students'] = len(group.user_set.all())
        result['student_structs'] = [
            student_struct(user)
            for user in group.user_set.all()
        ]
        result['student_structs'].sort(key=lambda struct: struct['display'])
        return result

    enriched_groups = [
        enriched_group(group)
        for group in coursedir.registered_groups.all()]
#    enriched_groups.sort(key=lambda eg: eg['number_students'])

    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        coursedir=coursedir,
        coursename=course,
        notebooks=notebooks,
        image=coursedir.image,
        static_mappings=coursedir.static_mappings,
        giturl=coursedir.giturl,
        tracks=coursedir.tracks(),
        enriched_groups=enriched_groups,
    )
    return render(request, "staff-course.html", env)


def render_subprocess_stream(
        request, course, subcommand, message, python, *args):
    """
    returns a HTML page that contains a call to /process/run
    so that the output gets streamed on the fly

    this can be either a call to
    * plain nbh (for code written in bash) with python=False
    * or to nbh-manage for code written in python
    """
    if not python:
        command = ["nbh", "-d", str(NBHROOT)]
    else:
        command = [ "nbh-manage" ]
    command += [subcommand, course] + list(args)

    command_json = json.dumps(command)
    command_string = " ".join(command)

    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        course=course,
        message=message,
        command_json=command_json,
        command_string=command_string,
    )
    template = "course-process.html"
    return render(request, template, env)


@staff_member_required
@csrf_protect
def update_from_git(request, course):
    return render_subprocess_stream(
        request, course, "course-update-from-git", 'updating git repo', False)


@staff_member_required
@csrf_protect
def build_image(request, course):
    return render_subprocess_stream(
        request, course, "course-build-image", 'rebuilding image', True)


@staff_member_required
@csrf_protect
def build_image_force(request, course):
    return render_subprocess_stream(
        request, course, "course-build-image", 'rebuilding image', True, "--force")


@staff_member_required
@csrf_protect
def clear_staff(request, course):
    coursedir = CourseDir.objects.get(coursename=course)
    return render_subprocess_stream(
        request, course, "course-clear-staff", 'clearing staff files',
        False, *coursedir.staffs)


@staff_member_required
@csrf_protect
def show_tracks(request, course):
    return render_subprocess_stream(
        request, course, "course-tracks", 'recomputing tracks', True)


@staff_member_required
@csrf_protect
def destroy_my_container(request, course):
    coursedir = get_object_or_404(CourseDir, coursename=course)
    killed = coursedir.kill_student_container(request.user.username)
    return HttpResponse(f"killing container for course {course}"
                        f" and student {request.user.username}"
                        f" returned {killed}"
                        f"<br>"
                        f"use the browser <- tool to go back"
                        )


def staff_course_update(request, course):
    coursedir = get_object_or_404(CourseDir, coursename=course)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UpdateCourseForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # here we just write it to the model field
            coursedir.autopull = form.cleaned_data['autopull']
            coursedir.archived = form.cleaned_data['archived']
            coursedir.autobuild = form.cleaned_data['autobuild']
            coursedir.image = form.cleaned_data['image']
            coursedir.staff_usernames = form.cleaned_data['staff_usernames']
            coursedir.save()

            # redirect to a new URL: xxx
            return HttpResponseRedirect(f"/staff/course/{course}")

    # If this is a GET (or any other method) create the default form.
    else:
        form = UpdateCourseForm(
            initial=dict(
                autopull=coursedir.autopull,
                autobuild=coursedir.autobuild,
                archived=coursedir.archived,
                image=coursedir.image,
                staff_usernames="\n".join(coursedir.staff_usernames.split()),
                ))

    env = dict(
        nbh_version=nbh_version,
        favicon_path=sitesettings.favicon_path,
        form=form,
        coursedir=coursedir,
        coursename=course)

    return render(request, 'staff-course-update.html', env)
