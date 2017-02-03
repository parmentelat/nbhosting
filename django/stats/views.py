import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from stats.stats import Stats

# Create your views here.
def top_link(html):
    return "<a class='top-link' href='/nbh/'>{html}</a>".format(html=html)

@login_required
@csrf_protect
def show_stats(request, course):

    return render(request, "stats.html", {
        'course': course,
    })

@csrf_protect
def send_metrics(request, course):
    stats = Stats(course)
    all_metrics = stats.metrics_per_day()
    result = json.dumps(all_metrics)
    return HttpResponse(result, content_type = "application/json")


csrf_protect
def send_counts(request, course):
    stats = Stats(course)
    counts = stats.counts_points()
    result = json.dumps(counts)
    return HttpResponse(result, content_type = "application/json")
