import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbhosting.stats.stats import Stats

# Create your views here.

@login_required
@csrf_protect
def show_stats(request, course):

    sections = []
    sections.append(dict(
        title = 'Progression',
        id = 'PROGRESSION',
        subsections = [
            { 'plotly_name' : 'plotly-nbstudents-per-notebook',
              'title' : 'Students per notebook',
#              'hide' : True,
            },
            { 'plotly_name' : 'plotly-nbstudents-per-nbnotebooks',
              'title' : 'Number of notebooks per student',
#              'hide' : True,
            },
            { 'plotly_name' : 'plotly-students',
              'title' : 'Students - who showed up at least once',
              'hide' : True,
            },
            { 'plotly_name' : 'plotly-notebooks',
              'title' : 'Notebooks - read at least once',
#              'hide' : True,
            },
        ]
    ))

    sections.append(dict(
        title = 'Details',
        id = 'DETAILS',
        subsections = [
            { 'plotly_name' : 'plotly-heatmap',
              'title' : 'Complete map',
              'hide' : True,
            },
        ]
    ))

    sections.append(dict(
        title = 'Activity',
        id = 'ACTIVITY',
        subsections = [
            { 'plotly_name' : 'plotly-containers-kernels',
              'title' : 'Jupyter containers and kernels',
             'hide' : True,
            },
        ]
    ))
    sections.append(dict(
        title = 'System',
        id = 'SYSTEM',
        subsections = [
            { 'plotly_name' : 'plotly-ds-percent',
              'title' : 'Free Disk Space %',
            },
            { 'plotly_name' : 'plotly-ds-free',
              'title' : 'Free Disk Space in Bytes',
            },
            { 'plotly_name' : 'plotly-cpu-load',
              'title' : 'CPU loads',
            },
        ]
    ))

    # set 'hide' to False by default
    for section in sections:
        for subsection in section['subsections']:
            subsection.setdefault('hide', False)
    
    env = dict(course=course, sections=sections)

    return render(request, "stats.html", env)

@csrf_protect
def send_daily_metrics(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.daily_metrics())
    return HttpResponse(encoded, content_type = "application/json")


@csrf_protect
def send_monitor_counts(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.monitor_counts())
    return HttpResponse(encoded, content_type = "application/json")


@csrf_protect
def send_material_usage(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.material_usage())
    return HttpResponse(encoded, content_type = "application/json")

@csrf_protect
def send_animated_attendance(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.animated_attendance())
    return HttpResponse(encoded, content_type = "application/json")
    
