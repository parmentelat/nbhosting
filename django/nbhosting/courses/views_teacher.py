# pylint: disable=missing-function-docstring
# pylint: disable=broad-except

"""
the views linked to the /teacher/* urls
"""

import json

from django.shortcuts import render, get_object_or_404

from django.http import (HttpResponse, QueryDict,
                         HttpResponseRedirect, HttpResponseBadRequest)
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbh_main.settings import logger

from nbhosting.courses.model_course import CourseDir
from nbhosting.courses.model_dropped import Dropped

from nbhosting.version import __version__ as nbh_version


######### teacher

@login_required
@csrf_protect
def teacher_droparea(request, course, droparea):
    coursedir = get_object_or_404(CourseDir, coursename=course)

    # xxx check user is a staff member

    # check the droparea is valid
    if droparea not in coursedir.dropareas():
        return HttpResponseRedirect(f"/staff/course/{course}")

    env = dict(
        coursedir=coursedir,
        coursename=course,
        droparea=droparea,
        droppeds=Dropped.scan_course_droparea(coursedir, droparea),
    )
    return render(request, 'teacher-droparea.html', env)

@csrf_protect
def teacher_dropped(request, course, droparea):
    coursedir = CourseDir.objects.get(coursename=course)
    if request.method == 'POST':
        # even when multiple files get dropped
        # simultaneously, we get called once per file
        # here's how to locate the instance of InMemoryUploadedFile
        inmemory = request.FILES['filepond']
        try:
            dropped = Dropped.from_uploaded(coursedir, droparea, inmemory)
            return HttpResponse(f"{dropped} uploaded, size={dropped.bytes_size}B")
        except Exception as exc:
            logger.exception("teacher_dropped could not upload")
            return HttpResponseBadRequest(f"{type(exc)}, could not upload, {exc}")
    elif request.method == 'DELETE':
        # https://stackoverflow.com/questions/4994789/django-where-are-the-params-stored-on-a-put-delete-request
        delete = QueryDict(request.body)
        relpath = list(delete.keys())[0]
        dropped = Dropped(coursedir, droparea, relpath)
        try:
            dropped.remove()
            return HttpResponse(f"{droparea}/{dropped.relpath} removed")
        except Exception as exc:
            logger.exception("teacher_dropped could not delete")
            return HttpResponseBadRequest(f"{type(exc)}, could not delete, {exc}")
    else:
        logger.exception(f"unsupported method {request.method}")
        return HttpResponseBadRequest("unsupported request method")


@csrf_protect
def teacher_dropped_push(request, course, droparea):
    """
    push one, several or all dropped files onto the registered students space

    incoming in request.POST.push:
      . '*' which means all known dropped
      . a single str
      . a list of str

    incoming in request.POST.dry_run:
      . missing or false: do the push
      . true: do not push, just return statistics
        (and then of course news=0)

    Result is a JSON-encoded list of dicts like this one
    [
       {
        'relpath': filename,
        'total': nb of students concerned,
        'availables': how many students have it now,
        'news': how many students actually have the newly pushed version}
       }
    ]
    """
    coursedir = CourseDir.objects.get(coursename=course)
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode())
            push = data['push']
            dry_run = data['dry_run']
            if push == '*':
                droppeds = Dropped.scan_course_droparea(coursedir, droparea)
            elif isinstance(push, list):
                droppeds = [Dropped(coursedir, droparea, relpath) for relpath in push]
            else:
                droppeds = [Dropped(coursedir, droparea, push)]
            result = []
            for dropped in droppeds:
                pushes = dropped.push_to_students(dry_run=dry_run)
                pushes['relpath'] = str(dropped.relpath)
                result.append(pushes)
            return HttpResponse(json.dumps(result))
        except Exception as exc:
            logger.exception("cannot teacher_dropped_push")
            return HttpResponseBadRequest(f"{type(exc)}, could not push, {exc}")
