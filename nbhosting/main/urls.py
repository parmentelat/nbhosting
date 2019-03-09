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

TRACK =     r'(?P<track>[\w_.-]*)'
COURSE =    r'(?P<course>[\w_.-]+)'
STUDENT =   r'(?P<student>[\w_.-]+)'
NOTEBOOK =  r'(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}'

COURSE_TRACK = rf'{COURSE}(:{TRACK})?'

urlpatterns = [
    # tweaking greedy and non greedy so that the .ipynb suffix
    # will go away if there's one or even two
    re_path(rf'^ipythonExercice/{COURSE}/{NOTEBOOK}/{STUDENT}$',
                        nbhosting.edxfront.views.edx_request
    ),
    re_path(rf'^ipythonShare/{COURSE}/{NOTEBOOK}/{STUDENT}$',
                        nbhosting.edxfront.views.share_notebook
    ),

    # regular users who log in
    re_path(rf'^auditor/courses.*$',
                        nbhosting.courses.views.auditor_list_courses),
    re_path(rf'^auditor/course/{COURSE_TRACK}$',
                        nbhosting.courses.views.auditor_show_course),
    re_path(rf'^auditor/notebook/{COURSE_TRACK}/{NOTEBOOK}$',
                        nbhosting.courses.views.auditor_show_notebook),
    re_path(rf'^auditor.*',
                        nbhosting.main.views.welcome),


    # super user
    re_path(rf'^staff/courses/update-from-git/{COURSE}$',
                        nbhosting.courses.views.update_from_git),
    re_path(rf'^staff/courses/build-image/{COURSE}$',
                        nbhosting.courses.views.build_image),
    re_path(rf'^staff/courses/clear-staff/{COURSE}$',
                        nbhosting.courses.views.clear_staff),
    re_path(rf'^staff/courses/show-tracks/{COURSE}$',
                        nbhosting.courses.views.show_tracks),
    re_path(rf'^staff/courses/.*',
                        nbhosting.courses.views.staff_list_courses),
    re_path(rf'^staff/course/{COURSE}$',
                        nbhosting.courses.views.staff_show_course),
    re_path(rf'^staff/stats/daily_metrics/{COURSE}$',
                        nbhosting.stats.views.send_daily_metrics),
    re_path(rf'^staff/stats/monitor_counts/{COURSE}$',
                        nbhosting.stats.views.send_monitor_counts),
    re_path(rf'^staff/stats/material_usage/{COURSE}$',
                        nbhosting.stats.views.send_material_usage),
    re_path(rf'^staff/stats/{COURSE}$',
                        nbhosting.stats.views.show_stats),
    re_path(rf'^staff.*',
                        nbhosting.main.views.welcome),
    # this one is not reachable through nginx, mostly for devel
    re_path(rf'^welcome.*',
                        nbhosting.main.views.welcome),

    # various redirects and other django-provided pages
    re_path(rf'^admin/',
                        admin.site.urls),
    re_path(rf'^accounts/login/',
                        auth_views.LoginView.as_view(), name='login'),
    re_path(rf'^accounts/logout/',
                        auth_views.LogoutView.as_view(), name='logout'),
    # path(rf'accounts/',          include('django.contrib.auth.urls')),
    # this seems to create a lot of issues, like bottomless recursions
    # probably better to handle this in nginx
    #re_path(rf'.*',
    #                    RedirectView.as_view(
    #                        url='welcome/', permanent=True),
    #                        name='welcome'),
]

from .settings import DEVEL
if DEVEL:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
