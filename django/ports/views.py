import os.path

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect

from ports.ports import PortPool

# Create your views here.
def top_link(html):
    return "<a class='top-link' href='/nbh/'>{html}</a>".format(html=html)

@csrf_protect
def list_ports(request):
    pool = PortPool()
    l_used = list(pool.used_ports)
    l_used.sort()
    html = top_link("<h1>Registered used ports</h1>")
    html += "<p>"
    for port in l_used:
        html += "<span class='port'>{}</span>".format(port)
    html += '</p>'
    html += '<p><a href="/nbh/ports/reset">Reset port mappings</a></p>'
    return HttpResponse(html)

def reset_ports(request):
    PortPool().reset()
    return HttpResponseRedirect("/nbh/ports")

