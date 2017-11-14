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

    section1 = {
        'title' : 'Progression',
        'id' : 'PROGRESSION',
        'subsections' : [
            { 'plotly_name' : 'plotly-students',
              'title' : 'Students - who showed up at least once'},
            { 'plotly_name' : 'plotly-nbstudents-per-notebook',
              'title' : 'Students per notebook'},
            { 'plotly_name' : 'plotly-nbstudents-per-nbnotebooks',
              'title' : 'Number of notebooks per student'},
            { 'plotly_name' : 'plotly-notebooks',
              'title' : 'Notebooks - read at least once',
              'hide' : True},
            { 'plotly_name' : 'plotly-heatmap',
              'title' : 'Complete map',
              'hide' : True},
            
        ]
    }
    section2 = {
        'title' : 'Activity',
        'id' : 'ACTIVITY',
        'subsections' : [
            { 'plotly_name' : 'plotly-containers-kernels',
              'title' : 'Jupyter containers and kernels'},
            # xxx student_homes as collected in counts
            # is not really useful so we don't show it anymore
        ]
    }
    section3 = {
        'title' : 'System',
        'id' : 'SYSTEM',
        'subsections' : [
            { 'plotly_name' : 'plotly-ds-percent',
              'title' : 'Disk Space Usage %'},
            { 'plotly_name' : 'plotly-ds-free',
              'title' : 'Free Space'},
            { 'plotly_name' : 'plotly-cpu-load',
              'title' : 'CPU loads'},
        ]
    }

    sections = [section1, section2, section3]
    # set 'hide' to False by default
    for section in sections:
        for subsection in section['subsections']:
            subsection.setdefault('hide', False)
    
    env = dict(course=course, sections=sections)

    return render(request, "stats.html", env)

@csrf_protect
def send_daily_metrics(request, course):
    stats = Stats(course)
    metrics = stats.daily_metrics()
    result = json.dumps(metrics)
    return HttpResponse(result, content_type = "application/json")


@csrf_protect
def send_monitor_counts(request, course):
    stats = Stats(course)
    counts = stats.monitor_counts()
    result = json.dumps(counts)
    return HttpResponse(result, content_type = "application/json")


@csrf_protect
def send_material_usage(request, course):
    stats = Stats(course)
    usage = stats.material_usage()
    result = json.dumps(usage)
    return HttpResponse(result, content_type = "application/json")
