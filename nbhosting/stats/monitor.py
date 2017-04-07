#!/usr/bin/env python3

from pathlib import Path
import time
import calendar
import json

import asyncio
import aiohttp

import docker

from nbhosting.main.settings import nbhosting_settings, logger
from nbhosting.courses.models import CourseDir
from nbhosting.stats.stats import Stats

"""
This processor is designed to be started as a systemd service

It will trigger on a cyclic basis - typically 15 minutes, and will
* spot and kill jupyter instances that have had no recent activity
* when an instance is killed, the stats/<course>/events.raw file
  is updated with a 'killing' line
* also writes into stats/<course>/counts.raw one line with the numbers
  of jupyter instances (running and frozen), and number of running kernels

---
* the notion of 'recent' activity is basic at the moment
  as of this first rough implem, nbh-run-student-course-jupyter touches a file
  named .monitor at the root of its jupyter space, and this is used as an indication 
  of the last activity

  *NOTE* : jupyter folks said that in v5 there will be some api
  to deal with that more accurately

"""


class CourseFigures:

    def __init__(self):
        self.frozen_containers = 0
        self.running_containers = 0
        self.running_kernels = 0

    def count_container(self, running: bool):
        if running:
            self.running_containers += 1
        else:
            self.frozen_containers += 1

    def count_kernels(self, count):
        self.running_kernels += count

        
class MonitoredJupyter:

    # container is an instance of
    # 
    def __init__(self,
                 container : docker.models.containers.Container,
                 course : str,
                 student : str,
                 figures : CourseFigures):
        self.container = container
        self.course = course
        self.student = student
        self.figures = figures

    def __str__(self):
        return "[Jupyter {}]".format(self.name)

    def name(self):
        return self.container.name

    def port_number(self):
        try:
            return int(self.container.attrs['NetworkSettings']
                       ['Ports']['8888/tcp'][0]['HostPort'])
        except Exception as e:
            logger.error("Cannot locate port number for {} - {}: {}"
                         .format(self, e, type(e)))
            return 0

    async def count_running_kernels(self):
        """
        updates
        * self.figures with number of running kernels
        * self.last_activity - a epoch/timestamp/nb of seconds
          may be None if using an old jupyter
        """
        port = self.port_number()
        if not port:
            return
        url = "http://localhost:{}/api/kernels?token={}"\
            .format(port, self.name())
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    json_str = await response.text()
            api_kernels = json.loads(json_str)
            nb_kernels = len(api_kernels)
            self.figures.count_kernels(nb_kernels)

            # jupyter 4 would not return this field
            # if with jupyter-5: look for the last_activity
            lasts = [
                api_kernel.get('last_activity', None)
                for api_kernel in api_kernels ]
            # filter out the ones that don't have it
            lasts = [last for last in lasts if last]
            # all kernels should have the flag
            if len(lasts) != nb_kernels:
                self.last_activity = None
            else:
                # compute overall last activity across kernels
                times = [
                    calendar.timegm(
                        time.strptime(last.replace('Z', 'UTC'),
                                      "%Y-%m-%dT%H:%M:%S.%f%Z"))
                    for last in lasts
                ]
                # if times is empty (no kernel): no activity
                self.last_activity = max(times, default=0)
                logger.debug("Found J5 last activity = {} with container {}"
                             .format(self.last_activity, self.name()))
                
        except Exception as e:
            logger.exception("Cannot probe number of kernels in {} - {}: {}"
                             .format(self.name(), type(e), e))
            self.last_activity = None


    async def co_run(self, grace):
        root = Path(nbhosting_settings['root'])
        name = self.container.name
        # stopped containers are useful only for statistics
        if self.container.status != 'running':
            self.figures.count_container(False)
            return
        # count number of kernels and last activity
        await self.count_running_kernels()
        # if using an old jupyter, let's resort to the old way
        # to get that info
        if not self.last_activity:
            logger.warning("Using jupyter4 method - i.e. using .monitor stamp"
                           "- with container {}".format(self.name()))
            try:
                stamp = root / "students" / self.student / self.course / ".monitor"
                self.last_activity = stamp.stat().st_mtime
                logger.debug("Found J4 last activity = {} with container {}"
                             .format(self.last_activity, self.name()))
            except FileNotFoundError as e:
                logger.info("container {} has no .monitor stamp - ignoring"
                            .format(name))
                return
        # check there has been activity in the last <grace> seconds
        last = self.last_activity
        now = time.time()
        grace_past = now - grace
        idle_minutes = (now - last) // 60
        if last > grace_past:
            logger.debug("sparing {} that had activity {}' ago"
                         .format(name, idle_minutes))
            self.figures.count_container(True)
        else:
            logger.info("container {} has been {} mn idle - killing"
                        .format(name, idle_minutes))
            # not sure what signal would be best ?
            self.container.kill()
            self.figures.count_container(False)
            Stats(self.course).record_kill_jupyter(self.student)

class Monitor:

    def __init__(self, grace, period):
        """
        All times in seconds

        Parameters:
            grace: is how long an idle server is kept running
            period: is how often the monitor runs
        """
        self.grace = grace
        self.period = period

    def run_once(self):
        try:
            proxy = docker.from_env()
            containers = proxy.containers.list(all=True)
        except Exception as e:
            logger.exception(
                "Cannot gather containers list at the docker daemon - skipping")
            return

        figures_per_course = {}

        # a list of async futures
        futures = []
        for container in containers:
            try:
                name = container.name
                logger.debug("monitoring container {}".format(name))
                course, student = name.split('-x-')
                figures_per_course.setdefault(course, CourseFigures())
                figures = figures_per_course[course]
                monitored_jupyter = MonitoredJupyter(container, course, student, figures)
                futures.append(monitored_jupyter.co_run(self.grace))
            # typically non-nbhosting containers
            except ValueError as e:
                # ignore this container as we don't even know
                # in what course it
                logger.info("ignoring non-nbhosting container {}"
                            .format(name))
        # run the whole stuff 
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(*futures))
        # write results
        for course, figures in figures_per_course.items():
            number_students = CourseDir(course).students_count()
            Stats(course).record_monitor_counts(
                figures.running_containers,
                figures.frozen_containers,
                figures.running_kernels,
                number_students,
            )

    def run_forever(self):
        tick = time.time()

        # one cycle can take some time as all the jupyters need to be http-probed
        # so let us compute the actual time to wait
        logger.info("nbh-monitor is starting up")
        while True:
            self.run_once()
            tick += self.period
            duration = max(0, int(tick - time.time()))
            logger.info("monitor is waiting for {}s".format(duration))
            time.sleep(duration)


