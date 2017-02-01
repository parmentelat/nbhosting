import json

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect

from stats.stats import Stats

# Create your views here.
def top_link(html):
    return "<a class='top-link' href='/nbh/'>{html}</a>".format(html=html)

@csrf_protect
def show_stats(request, course):
    html = top_link("<h1>Stats for course {}</h1>".format(course))
    html += '''
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/metrics-graphics/2.11.0/metricsgraphics.min.js"></script>
<style type="text/css">@import url("https://cdnjs.cloudflare.com/ajax/libs/metrics-graphics/2.11.0/metricsgraphics.css"); </style>
<!-- students -->
<h1>Students</h1>
<div  id="stats-students"></div>
<span id="legend-students"></span>
<!-- notebooks -->
<h1>Notebooks</h1>
<div  id="stats-notebooks"></div>
<span id="legend-notebooks"></span>
<!-- notebooks -->
<h1>Jupyters</h1>
<div  id="stats-jupyters"></div>
<span id="legend-jupyters"></span>
<!-- end -->
<script>
var url_metrics="/nbh/stats/metrics/{course}";
d3.request(url_metrics, function (error, response) {
    var incoming = JSON.parse(response.response);
    //console.log(incoming);
    // incoming has 4 arrays
    var students        = MG.convert.date(incoming[0], 'date');
    var students_cumul  = MG.convert.date(incoming[1], 'date');
    var notebooks       = MG.convert.date(incoming[2], 'date');
    var notebooks_cumul = MG.convert.date(incoming[3], 'date');
    MG.data_graphic({
        data: [ students, students_cumul ],
        target:        document.getElementById('stats-students'),
        legend_target: document.getElementById('legend-students'),
        legend: ["per day", "cumulative"],
        title: "Connected students",
        description: "per day, and cumulative",
        width: 900,
        height: 400,
        right: 50,
    });
    MG.data_graphic({
        data: [ notebooks, notebooks_cumul ],
        target:        document.getElementById('stats-notebooks'),
        legend_target: document.getElementById('legend-notebooks'),
        legend: ["per day", "cumulative"],
        title: "Opened notebooks",
        description: "per day, and cumulative",
        width: 900,
        height: 400,
        right: 50,
    });
});
var url_counts="/nbh/stats/counts/{course}";
d3.request(url_counts, function (error, response) {
    var incoming = JSON.parse(response.response);
    console.log(incoming[0]);
    // incoming has 1 array
    var jupyters        = MG.convert.date(incoming[0], 'date', '%Y-%m-%d %H:%M:%S');
    MG.data_graphic({
        data: [ jupyters ],
        target:        document.getElementById('stats-jupyters'),
        legend_target: document.getElementById('legend-jupyters'),
        legend: ["opened"],
        title: "Running jupyters",
        description: "instantaneous",
        width: 900,
        height: 400,
        right: 50,
    });
});
</script> 
'''.replace('{course}', course)
    return HttpResponse(html)


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
