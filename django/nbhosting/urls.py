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

import edxfront.views
import nbhosting.views
import courses.views
import stats.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # tweaking greedy and non greedy so that the .ipynb suffix go away if there's one or even two
    url(r'^ipythonExercice/(?P<course>[\w_.-]+)/(?P<notebook>[-\w_\+/\.]+?)(.ipynb){0,2}/(?P<student>[\w_.-]+)$',
        edxfront.views.edx_request
    ),
    url(r'^nbh/login/$',                                        auth_views.login, name='login'),
    url(r'^nbh/logout/$',                                       auth_views.logout, name='logout'),
    url(r'^nbh/admin/',                                         admin.site.urls),
    url('^nbh/accounts/',                                       include('django.contrib.auth.urls')),
    # our stuff
    url(r'^nbh/courses/update/(?P<course>[\w_.-]+)',            courses.views.update_course),
    url(r'^nbh/courses',                                        courses.views.list_courses),
    url(r'^nbh/course/(?P<course>[\w_.-]+)',                    courses.views.list_course),
    url(r'^nbh/stats/daily_metrics/(?P<course>[\w_.-]+)',       stats.views.send_daily_metrics),
    url(r'^nbh/stats/monitor_counts/(?P<course>[\w_.-]+)',      stats.views.send_monitor_counts),
    url(r'^nbh/stats/(?P<course>[\w_.-]+)',                     stats.views.show_stats),
    url(r'^nbh',                                                nbhosting.views.welcome),
]
