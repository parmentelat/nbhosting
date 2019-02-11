"""
nbhosting URL Configuration
"""

# pylint: disable=c0326, c0330

from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

# import nbhosting.main.views
import nbhosting.edxfront.views
import nbhosting.courses.views
import nbhosting.stats.views
import nbhosting.main.views

urlpatterns = [
    # tweaking greedy and non greedy so that the .ipynb suffix
    # will go away if there's one or even two
    re_path(r'^ipythonExercice/(?P<course>[\w_.-]+)/'
         r'(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
                        nbhosting.edxfront.views.edx_request
    ),
    re_path(r'^ipythonShare/(?P<course>[\w_.-]+)/'
         r'(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
                        nbhosting.edxfront.views.share_notebook
    ),

    # regular users who log in
    re_path(r'^auditor/courses.*$',
                        nbhosting.courses.views.auditor_list_courses),
    re_path(r'^auditor/course/(?P<course>[\w_.-]+)$',
                        nbhosting.courses.views.auditor_show_course),
    re_path(r'^auditor.*',
                        nbhosting.main.views.welcome),


    # super user
    re_path(r'staff/courses/update-from-git/(?P<course>[\w_.-]+)$',
                        nbhosting.courses.views.update_from_git),
    re_path(r'staff/courses/build-image/(?P<course>[\w_.-]+)$',
                        nbhosting.courses.views.build_image),
    re_path(r'staff/courses/clear-staff/(?P<course>[\w_.-]+)$',
                        nbhosting.courses.views.clear_staff),
    re_path(r'staff/courses/.*',
                        nbhosting.courses.views.staff_list_courses),
    re_path(r'staff/course/(?P<course>[\w_.-]+)$',
                        nbhosting.courses.views.staff_show_course),
    re_path(r'staff/stats/daily_metrics/(?P<course>[\w_.-]+)$',
                        nbhosting.stats.views.send_daily_metrics),
    re_path(r'staff/stats/monitor_counts/(?P<course>[\w_.-]+)$',
                        nbhosting.stats.views.send_monitor_counts),
    re_path(r'staff/stats/material_usage/(?P<course>[\w_.-]+)$',
                        nbhosting.stats.views.send_material_usage),
    re_path(r'staff/stats/(?P<course>[\w_.-]+)$',
                        nbhosting.stats.views.show_stats),
    re_path(r'staff.*',
                        nbhosting.main.views.welcome),
    # this one is not reachable through nginx, mostly for devel
    re_path(r'^welcome.*',
                        nbhosting.main.views.welcome),

    # various redirects and other django-provided pages
    path(r'admin/',
                        admin.site.urls),
    path(r'accounts/login/',
                        auth_views.LoginView.as_view(), name='login'),
    path(r'accounts/logout/',
                        auth_views.LogoutView.as_view(), name='logout'),
    # path(r'accounts/',          include('django.contrib.auth.urls')),
    re_path(r'.*',
                        RedirectView.as_view(
                            url='welcome/', permanent=True),
                            name='welcome'),
]
