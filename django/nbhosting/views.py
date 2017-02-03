import os.path
import subprocess

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def welcome(request):
    html = """
<h1>Welcome to nbhosting</h1>
<ul>
<li> <a href="/nbh/courses">Courses</a></li>
<li> <a href="/nbh/students">Students (Not Yet Implemented)</a></li>
"""
    return HttpResponse(html)
    