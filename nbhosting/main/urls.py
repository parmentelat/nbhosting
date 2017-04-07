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

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

import nbhosting.main.views
import nbhosting.edxfront.views
import nbhosting.courses.views
import nbhosting.stats.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # tweaking greedy and non greedy so that the .ipynb suffix go away if there's one or even two
    url(r'^ipythonExercice/(?P<course>[\w_.-]+)/(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
        nbhosting.edxfront.views.edx_request
    ),
    url(r'^nbh/login/$',                                        auth_views.login, name='login'),
    url(r'^nbh/logout/$',                                       auth_views.logout, name='logout'),
    url(r'^nbh/admin/',                                         admin.site.urls),
    url('^nbh/accounts/',                                       include('django.contrib.auth.urls')),
    # our stuff
    url(r'^nbh/courses/update/(?P<course>[\w_.-]+)',            nbhosting.courses.views.update_course),
    url(r'^nbh/courses',                                        nbhosting.courses.views.list_courses),
    url(r'^nbh/course/(?P<course>[\w_.-]+)',                    nbhosting.courses.views.list_course),
    url(r'^nbh/stats/daily_metrics/(?P<course>[\w_.-]+)',       nbhosting.stats.views.send_daily_metrics),
    url(r'^nbh/stats/monitor_counts/(?P<course>[\w_.-]+)',      nbhosting.stats.views.send_monitor_counts),
    url(r'^nbh/stats/(?P<course>[\w_.-]+)',                     nbhosting.stats.views.show_stats),
    url(r'^nbh',                                                nbhosting.main.views.welcome),
]
