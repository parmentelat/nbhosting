from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

@login_required
@csrf_protect
def welcome(request):
    return render(request, 'welcome.html')
