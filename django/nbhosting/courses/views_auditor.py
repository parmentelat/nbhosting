# pylint: disable=c0111, w1203

import re

from django.shortcuts import render, get_object_or_404

#from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbh_main.settings import logger

from nbhosting.courses.model_course import CourseDir

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
