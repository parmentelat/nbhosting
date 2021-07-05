# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring

from django.contrib import admin

# Register your models here.

#from django import forms
#from django.contrib.admin.widgets import FilteredSelectMultiple

#from django.contrib.auth.models import User, Group
from .model_course import CourseDir


@admin.register(CourseDir)
class CourseDirAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['giturl', 'image']}),
        ('boolean flags',
         {'fields': [ 'autopull', 'autobuild', 'archived']}),
        ('staff', {'fields': ['staff_usernames']}),
        ('groups', {'fields': ['registered_groups']}),
    ]
