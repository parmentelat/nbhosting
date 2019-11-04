"""
nbhosting URL Configuration
"""

# pylint: disable=c0326, c0330

from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

import nbhosting.edxfront.views
import nbhosting.courses.views
import nbhosting.stats.views
import nbh_main.views

TRACK =       r'(?P<track>[^/]*)'
COURSE =      r'(?P<course>[\w_.-]+)'
STUDENT =     r'(?P<student>[\w_.-]+)'
# being very loose / flexible for the spelling of <notebook>
# (for supporting e.g. spaces in filenames)
# requires the non-greedy version of .+
# because otherwise the .ipynb stuff goes into <notebook> as well
NOTEBOOK =    r'(?P<notebook>.+?)(\.ipynb){0,2}'
JUPYTER_URL = r'(?P<jupyter_url>.*)?'

JUPYTER_APP = r'(?P<jupyter_app>(classic)|(jlab))'
COURSE_TRACK = rf'{COURSE}(:{TRACK})?(@{JUPYTER_APP})?'

urlpatterns = [
    # can't change this one as FUN and M@gistere depend on it
    re_path(rf'^ipythonExercice/{COURSE}/{NOTEBOOK}/{STUDENT}/?$',
                        nbhosting.edxfront.views.edx_request),
    # used internally to produce snapshots
    re_path(rf'^ipythonShare/{COURSE}/{NOTEBOOK}/{STUDENT}/?$',
                        nbhosting.edxfront.views.share_notebook),
    # new name for ipythonExercice, should be used from now on
    re_path(rf'^notebookLazyCopy/{COURSE}/{NOTEBOOK}/{STUDENT}/?$',
                        nbhosting.edxfront.views.edx_request),
    re_path(rf'^notebookGitRepo/{COURSE}/{NOTEBOOK}/{STUDENT}/?$',
                        nbhosting.edxfront.views.classroom_request),
    # /ipythonForward/thecourse/thestudent/tree
    # /ipythonForward/thecourse/thestudent/lab
    # /ipythonForward/thecourse/thestudent/git-pull?repo=...
    re_path(rf'^ipythonForward/{COURSE}/{STUDENT}/{JUPYTER_URL}/?$',
                        nbhosting.edxfront.views.jupyterdir_forward
    ),

    # regular users who log in
    re_path(rf'^auditor/courses.*$',
                        nbhosting.courses.views.auditor_list_courses),
    # this now is the foremost interface to a course
    re_path(rf'^auditor/notebook/{COURSE_TRACK}(/{NOTEBOOK})?/?$',
                        nbhosting.courses.views.auditor_show_notebook),
    # more harmful than helpful at least during devel
    re_path(rf'^auditor.*',
                        nbh_main.views.welcome),

    # super user
    re_path(rf'^staff/courses/update-from-git/{COURSE}/?$',
                        nbhosting.courses.views.update_from_git),
    re_path(rf'^staff/courses/build-image/{COURSE}/?$',
                        nbhosting.courses.views.build_image),
    re_path(rf'^staff/courses/destroy-my-container/{COURSE}/?$',
                        nbhosting.courses.views.destroy_my_container),
    re_path(rf'^staff/courses/clear-staff/{COURSE}/?$',
                        nbhosting.courses.views.clear_staff),
    re_path(rf'^staff/courses/show-tracks/{COURSE}/?$',
                        nbhosting.courses.views.show_tracks),
    re_path(rf'^staff/courses.*',
                        nbhosting.courses.views.staff_list_courses),
    re_path(rf'^staff/course/{COURSE}/update/?$',
                        nbhosting.courses.views.staff_course_update,
                        name="course-update"),
    re_path(rf'^staff/course/{COURSE}/?$',
                        nbhosting.courses.views.staff_show_course),
    re_path(rf'^staff/stats/daily_metrics/{COURSE}/?$',
                        nbhosting.stats.views.send_daily_metrics),
    re_path(rf'^staff/stats/monitor_counts/{COURSE}/?$',
                        nbhosting.stats.views.send_monitor_counts),
    re_path(rf'^staff/stats/material_usage/{COURSE}/?$',
                        nbhosting.stats.views.send_material_usage),
    re_path(rf'^staff/stats/{COURSE}/?$',
                        nbhosting.stats.views.show_stats),
    re_path(rf'^staff.*',
                        nbh_main.views.welcome),
    # this one is not reachable through nginx, mostly for devel
    re_path(rf'^welcome.*',
                        nbh_main.views.welcome),
    # empty url
    re_path(rf'^$',
                        nbh_main.views.welcome),

    # various redirects and other django-provided pages
    re_path(rf'^admin/',
                        admin.site.urls),
    re_path(rf'^accounts/login/',
                        auth_views.LoginView.as_view(), name='login'),
    re_path(rf'^accounts/logout/',
            nbh_main.views.logout, name='logout'),
    path(rf'accounts/',          include('django.contrib.auth.urls')),
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
