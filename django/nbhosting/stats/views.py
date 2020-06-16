import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from nbhosting.stats.stats import Stats

# Create your views here.

@staff_member_required
@csrf_protect
def show_stats(request, course):

    sections = []
    sections.append(dict(
        title = 'Progression',
        id = 'PROGRESSION',
        subsections = [
            { 'div_id' : 'plotly-nbstudents-per-notebook',
              'title' : 'Students per notebook',
              'hide' : True,
            },
            { 'div_id' : 'd3-nb-students-per-notebook',
              'title' : 'Students per notebook - animation',
              'engine': 'd3',
              # 'hide' : True,
            },
            { 'div_id' : 'plotly-nbstudents-per-nbnotebooks',
              'title' : 'Number of notebooks per student',
              'hide' : True,
            },
            { 'div_id' : 'plotly-students',
              'title' : 'Students who showed up at least once',
              'hide' : True,
            },
            { 'div_id' : 'plotly-notebooks',
              'title' : 'Notebooks read at least once',
              'hide' : True,
            },
        ]
    ))

    sections.append(dict(
        title = 'Details',
        id = 'DETAILS',
        subsections = [
            { 'div_id' : 'plotly-heatmap',
              'title' : 'Complete map',
              'hide' : True,
            },
        ]
    ))

    sections.append(dict(
        title = 'Activity',
        id = 'ACTIVITY',
        subsections = [
            { 'div_id' : 'plotly-containers-kernels',
              'title' : 'Jupyter containers and kernels',
              'hide' : True,
            },
        ]
    ))
    sections.append(dict(
        title = 'System',
        id = 'SYSTEM',
        subsections = [
            { 'div_id' : 'plotly-ds-percent',
              'title' : 'Free Disk Space %',
              'hide' : True,
            },
            { 'div_id' : 'plotly-ds-free',
              'title' : 'Free Disk Space in Bytes',
              'hide' : True,
            },
            { 'div_id' : 'plotly-cpu-load',
              'title' : 'CPU loads',
              'hide' : True,
            },
            {'div_id' : 'plotly-memory',
             'title' : 'Memory Usage in %',
             'hide' : True,
             },
        ]
    ))

    # set 'hide' to False by default
    for section in sections:
        for subsection in section['subsections']:
            subsection.setdefault('engine', 'plotly')
            subsection.setdefault('hide', False)

    # propagate server_name to html template
    server_name = request.META['SERVER_NAME'].split('.')[0]

    env = dict(coursename=course, sections=sections, server_name=server_name)

    return render(request, "stats.html", env)


@csrf_protect
def send_daily_metrics(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.daily_metrics())
    response = HttpResponse(encoded, content_type="application/json")
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_protect
def send_monitor_counts(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.monitor_counts())
    response = HttpResponse(encoded, content_type="application/json")
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_protect
def send_material_usage(request, course):
    stats = Stats(course)
    encoded = json.dumps(stats.material_usage())
    response = HttpResponse(encoded, content_type="application/json")
    response['Access-Control-Allow-Origin'] = '*'
    return response
