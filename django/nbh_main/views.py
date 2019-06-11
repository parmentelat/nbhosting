from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from nbhosting.version import __version__ as nbh_version


@csrf_protect
def welcome(request):
#    that welcome page is for devel purposes only
    return render(request, 'welcome.html',
                  dict(nbh_version=nbh_version))
#    return HttpResponseRedirect('/staff/courses')
