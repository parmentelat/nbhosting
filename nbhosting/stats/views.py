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
            { 'plotly_name' : 'stats-students',
              'title' : 'Students - who showed up at least once'},
            { 'plotly_name' : 'stats-notebooks',
              'title' : 'Notebooks - read at least once'},
        ]
    }
    section2 = {
        'title' : 'Activity',
        'id' : 'ACTIVITY',
        'subsections' : [
            { 'plotly_name' : 'stats-jupyters',
              'title' : 'Jupyter containers'},
            { 'plotly_name' : 'stats-kernels',
              'title' : 'Running kernels'},
            { 'plotly_name' : 'stats-student-counts',
              'title' : 'Students with a homedir'},
        ]
    }
    section3 = {
        'title' : 'System',
        'id' : 'SYSTEM',
        'subsections' : [
            { 'plotly_name' : 'stats-ds-percent',
              'title' : 'Disk Space Usage %'},
            { 'plotly_name' : 'stats-ds-free',
              'title' : 'Free Space'},
            { 'plotly_name' : 'stats-cpu-load',
              'title' : 'CPU loads'},
        ]
    }
    env = { 'course' : course,
            'sections' : [section1, section2, section3] }

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
