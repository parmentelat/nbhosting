"""
nbhosting URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

# pylint: disable=c0326, c0330

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

import nbhosting.main.views
import nbhosting.edxfront.views
import nbhosting.courses.views
import nbhosting.stats.views

urlpatterns = [                                         # pylint: disable=c0103
    url(r'^admin/', admin.site.urls),
    # tweaking greedy and non greedy so that the .ipynb suffix
    # will go away if there's one or even two
    url(r'^ipythonExercice/(?P<course>[\w_.-]+)/'
        r'(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
        nbhosting.edxfront.views.edx_request
    ),
    url(r'^ipythonShare/(?P<course>[\w_.-]+)/'
        r'(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
        nbhosting.edxfront.views.share_notebook
    ),
# changed for django 2.1
# https://docs.djangoproject.com/en/2.1/topics/auth/default/
    url(r'^nbh/login/$',
                                auth_views.LoginView.as_view(), name='login'),
    url(r'^nbh/logout/$',
                                auth_views.LogoutView.as_view(), name='logout'),
    url(r'^nbh/admin/',
                                admin.site.urls),
    url('^nbh/accounts/',
                                include('django.contrib.auth.urls')),
    # our stuff
    url(r'^nbh/courses/update-from-git/(?P<course>[\w_.-]+)',
                                nbhosting.courses.views.update_from_git),
    url(r'^nbh/courses/build-image/(?P<course>[\w_.-]+)',
                                nbhosting.courses.views.build_image),
    url(r'^nbh/courses/clear-staff/(?P<course>[\w_.-]+)',
                                nbhosting.courses.views.clear_staff),
    url(r'^nbh/courses',
                                nbhosting.courses.views.list_courses),
    url(r'^nbh/course/(?P<course>[\w_.-]+)',
                                nbhosting.courses.views.list_course),
    url(r'^nbh/stats/daily_metrics/(?P<course>[\w_.-]+)',
                                nbhosting.stats.views.send_daily_metrics),
    url(r'^nbh/stats/monitor_counts/(?P<course>[\w_.-]+)',
                                nbhosting.stats.views.send_monitor_counts),
    url(r'^nbh/stats/material_usage/(?P<course>[\w_.-]+)',
                                nbhosting.stats.views.send_material_usage),
    url(r'^nbh/stats/(?P<course>[\w_.-]+)',
                                nbhosting.stats.views.show_stats),
    url(r'^nbh',
                                nbhosting.main.views.welcome),
]
