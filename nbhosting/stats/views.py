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

    return render(request, "stats.html", {
        'course': course,
    })

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
