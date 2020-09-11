# pylint: disable=c0111, w1203

import re

from django.shortcuts import render, get_object_or_404

#from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from nbh_main.settings import logger

from nbhosting.courses.model_course import CourseDir
from nbhosting.courses.model_track import Notebook
from nbhosting.courses.forms import UpdateCourseForm

from nbhosting.version import __version__ as nbh_version


def match(coursename, pattern):
    print(f"match {coursename} {pattern}")
    pieces = pattern.split('|')
    for piece in pieces:
        print(f"piece={piece}")
        if re.search(piece, coursename):
            return True
    return False

######### auditor

@login_required
@csrf_protect
def auditor_list_courses(request):
    course_dirs = CourseDir.objects.order_by('coursename')
    course_dirs = [cd for cd in course_dirs if not cd.archived]
    pattern = request.GET.get('pattern', None)
    if pattern:
        course_dirs = [coursedir for coursedir in course_dirs 
                       if match(coursedir.coursename, pattern)]
    # all=true - or anything really means show all courses
    ask_all_courses = request.GET.get('all', None)
    show_all_courses = True
    if ask_all_courses is None:
        groups = request.user.groups.all()
        if groups:
            show_all_courses = False
            course_dirs = [coursedir for coursedir in course_dirs
                           if coursedir.relevant(request.user)
                              and not coursedir.archived]
    env = dict(
        course_dirs=course_dirs,
        nbh_version=nbh_version,
        show_all_courses = show_all_courses,
    )

    return render(request, "auditor-courses.html", env)


@login_required
@csrf_protect
def auditor_show_notebook(request, course, notebook=None, track=None, 
                          jupyter_app=None):
    """
    the auditor notebook view has 2 major modes;
    either a jupyter app is selected, or a track is selected
    in the latter case a notebook can be passed as well
    
    we should have either
    * jupyter_app set to ' classic' or 'jlab' 
      in that case, track and notebook are totally discarded
    * otherwise if jupyter_app is not set, 
      then we may have track set to a trackname
      and if not, we select the first track in the course
      in that case (no jupyter_app) a notebook arg can be passed
      it is then interpreted as a path from the git repo root
    """

    logger.info(f"auditor_show_notebook track={track} jupyter_app={jupyter_app} "
                f"notebook={notebook}")

    student = request.user.username

    # don't want to mess with the urls
    trackname = track
    
    
    coursedir = get_object_or_404(CourseDir, coursename=course)
    
    # do this in both jupyter and track mode
    if not trackname:
        trackname = coursedir.default_trackname()
    track = coursedir.track(trackname)

    if notebook is None:
        notebook_obj = track.first_notebook()
        notebook = notebook_obj.clean_path()
        print(f"default notebook -> {notebook}")
    else:
        notebook_obj = track.spot_notebook(notebook)

    # compute title as notebookname if found in sections
    if jupyter_app == 'classic':
        title = 'Jupyter classic'
        iframe = f'/ipythonForward/{course}/{student}/tree'
    elif jupyter_app == 'jlab':
        title = 'Jupyter lab'
        iframe = f'/ipythonForward/{course}/{student}/lab'

    else:
        title = notebook_obj.notebookname if notebook_obj else notebook
        iframe = f"/notebookGitRepo/{course}/{notebook}/{student}"
    
#    giturl = coursedir.giturl
#    gitpull_url = (f"/ipythonForward/{course}/{student}/git-pull"
#                   f"?repo={giturl}"
#                   f"&autoRedirect=false"
#                   f"&toplevel=."
#                   f"&redirectUrl={iframe}"
#                   )
    tracks = coursedir.tracks()
    for track_obj in tracks:
        track_obj.mark_notebooks(student)
        
    first_notebook_per_track = {
        track_obj.id : track_obj.first_notebook().clean_path()
        for track_obj in tracks
    }

    env = dict(
        nbh_version=nbh_version,
        coursename=course,
        student=student,
        coursedir=coursedir,
        track=track,
        jupyter_app=jupyter_app,
        notebook=notebook,
        iframe=iframe,
#        gitpull_url=gitpull_url,
        head_title=f"nbh:{course}",
        title=title,
        tracks=tracks,
        first_notebook_per_track=first_notebook_per_track,
    )

    return render(request, "auditor-notebook.html", env)


######### staff

@staff_member_required
@csrf_protect
def staff_list_courses(request):
    course_dirs = CourseDir.objects.order_by('coursename')
    env = dict(
        nbh_version=nbh_version,
        course_dirs=course_dirs,
    )
    return render(request, "staff-courses.html", env)

@staff_member_required
@csrf_protect
def staff_show_course(request, course):
    coursedir = CourseDir.objects.get(coursename=course)
    print(f"in staff_show_course: {hasattr(coursedir, 'image')}")
    coursedir.probe()
    notebooks = list(coursedir.notebooks())
    notebooks.sort()
    # shorten staff hashes

    def shorten(staff):
        if len(staff) >= 10:
            return f"{staff[:7]}..."
        else:
            return staff


    shorten_staffs = [shorten(username)
                     for username in   coursedir.staff_usernames.split()]
    shorten_staffs.sort()

    def enriched_group(group):
        def student_struct(user):
            return {
                'display': user.username,
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
        coursedir=coursedir,
        coursename=course,
        notebooks=notebooks,
        image=coursedir.image,
        static_mappings=coursedir.static_mappings,
        shorten_staffs=shorten_staffs,
        giturl=coursedir.giturl,
        tracks=coursedir.tracks(),
        enriched_groups=enriched_groups,
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
    coursedir = CourseDir.objects.get(coursename=course)
    completed = coursedir.nbh_subprocess(subcommand, python, *args)
    command = " ".join(completed.args)
    # expose most locals, + the attributes of completed
    # like stdout and stderr
    env = dict(
        nbh_version=nbh_version,
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
    coursedir = CourseDir.objects.get(coursename=course)
    return render_subprocess_result(
        request, course,
        f"course-clear-staff", 'staff files cleared', False,
        *coursedir.staff_usernames.split())


@staff_member_required
@csrf_protect
def show_tracks(request, course):
    return render_subprocess_result(
        request, course,
        "course-tracks", 'tracks recomputed', True)


@staff_member_required
@csrf_protect
def destroy_my_container(request, course):
    print("in view destroy_my_container")
    return render_subprocess_result(
        request, course,
        "course-destroy-student-container", "my container destroyed",
        True, request.user.username)


def staff_course_update(request, course):
    print(f"MATCHED staff-course.html with course={course}")
    coursedir = get_object_or_404(CourseDir, coursename=course)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UpdateCourseForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            coursedir.autopull = form.cleaned_data['autopull']
            coursedir.archived = form.cleaned_data['archived']
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
                archived=coursedir.archived,
                image=coursedir.image,
                staff_usernames="\n".join(coursedir.staff_usernames.split()),
                ))

    env = dict(
        nbh_version=nbh_version,
        form=form,
        coursedir=coursedir,
        coursename=course)

    return render(request, 'staff-course-update.html', env)
