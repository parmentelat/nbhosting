#!/usr/bin/env python3

import os
import time
import calendar
import json
from pathlib import Path
import subprocess
import logging

import asyncio
import aiohttp

import docker

from nbhosting.main.settings import sitesettings
# redirect into monitor.log
from nbhosting.main.settings import monitor_logger as logger
from nbhosting.courses.models import CourseDir, CoursesDir
from nbhosting.stats.stats import Stats

"""
This processor is designed to be started as a systemd service

It will trigger on a cyclic basis - typically 15 minutes, and will
* spot and kill jupyter instances that have had no recent activity
* when an instance is killed, the stats/<course>/events.raw file
  is updated with a 'killing' line
* also writes into stats/<course>/counts.raw one line with the numbers
  of jupyter instances (running and frozen), and number of running kernels

Also note that
* the notion of 'recent' activity takes advantage of a feature introduced
  in jupyter5, where the /api/kernels/ call returns for each kernel its last activity

"""


class CourseFigures:

    def __init__(self):
        self.frozen_containers = 0
        self.running_containers = 0
        self.running_kernels = 0

    # to avoid counting kernels in containers that get killed
    # we count updateboth counters at the same time
    # of course nb_kernels is meaningful only if running is True
    def count_container(self, running: bool, nb_kernels: int = 0):
        if running:
            self.running_containers += 1
            # nb_kernels may be None
            self.running_kernels += (nb_kernels or 0)
        else:
            self.frozen_containers += 1

class MonitoredJupyter:

    # container is an instance of
    # 
    def __init__(self,
                 container : docker.models.containers.Container,
                 course : str,
                 student : str,
                 figures : CourseFigures,
                 # the hash of the expected image - may be None
                 hash : str):
        self.container = container
        self.course = course
        self.student = student
        self.figures = figures
        self.hash = hash
        self.nb_kernels = None

    def __str__(self):
        return "container {} [{}k]".format(self.name, self.nb_kernels)

    # docker containers have a value 'name', so it's confusing
    # to access it through a method
    @property
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
        updates:
        * self.figures with number of running kernels
        * self.last_activity - a epoch/timestamp/nb of seconds
          may be None if using an old jupyter
        """
        port = self.port_number()
        if not port:
            return
        url = "http://localhost:{}/api/kernels?token={}"\
            .format(port, self.name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    json_str = await response.text()
            api_kernels = json.loads(json_str)
            self.nb_kernels = len(api_kernels)

            # note: jupyter 4 would not return this field
            lasts = [
                api_kernel.get('last_activity', None)
                for api_kernel in api_kernels ]
            # filter out the ones that don't have it
            lasts = [last for last in lasts if last]
            # all kernels should have the flag
            if len(lasts) != self.nb_kernels:
                logger.error("found {} last activities for {} kernels\n"
                             "are you using jupyter <= 4 ?\n"
                             "containers can't be properly cleaned up.."
                             .format(len(lasts), self.nb_kernels))
                self.last_activity = None
                return
            # compute overall last activity across kernels
            times = [
                calendar.timegm(
                    time.strptime(last.replace('Z', 'UTC'),
                                  "%Y-%m-%dT%H:%M:%S.%f%Z"))
                for last in lasts
            ]
            # if times is empty (no kernel): no activity
            self.last_activity = max(times, default=0)
                
        except Exception as e:
            logger.exception("Cannot probe number of kernels in {} - {}: {}"
                             .format(self, type(e), e))
            self.last_activity = None


    async def co_run(self, grace):
        root = Path(sitesettings.root)
        # stopped containers are useful only for statistics
        if self.container.status != 'running':
            self.figures.count_container(False)
            return
        # count number of kernels and last activity
        await self.count_running_kernels()
        # if using an old jupyter, let's resort to the old way
        # to get that info
        if not self.last_activity:
            logger.error("skipping container {} with no known last_activity".format(self.name))
            return
        # check there has been activity in the last <grace> seconds
        now = time.time()
        grace_past = now - grace
        idle_minutes = (now - self.last_activity) // 60
        if self.last_activity > grace_past:
            logger.debug("sparing {} that had activity {}' ago"
                         .format(self, idle_minutes))
            self.figures.count_container(True, self.nb_kernels)
        else:
            logger.info("{} has been idle for {} mn - killing"
                        .format(self, idle_minutes))
            # kill it
            self.container.kill()
            # if that container does not run the expected image hash
            # it is because the course image was upgraded in the meanwhile
            # then we even remove the container so it will get re-created
            # next time with the right image this time
            actual_hash = self.container.image.id
            if actual_hash != self.hash:
                logger.info("removing container {} that has hash {} instead of expected {}"
                            .format(self.name, actual_hash, self.hash))
                self.container.remove(v=True)
            # this counts for one dead container
            self.figures.count_container(False)
            # keep track or that removal in events.raw
            Stats(self.course).record_kill_jupyter(self.student)

class Monitor:

    def __init__(self, grace, period, debug):
        """
        All times in seconds

        Parameters:
            grace: is how long an idle server is kept running
            period: is how often the monitor runs
        """
        self.grace = grace
        self.period = period
        if debug:
            logger.setLevel(logging.DEBUG)

    def run_once(self):

        # initialize all known courses - we want data on courses
        # even if they don't run any container yet 
        logger.debug("scanning courses")
        coursesdir = CoursesDir()
        coursenames = coursesdir.coursenames()
        figures_by_course = {coursename : CourseFigures() 
                             for coursename in coursenames}

        try:
            proxy = docker.from_env(version='auto')
            logger.debug("scanning containers")
            containers = proxy.containers.list(all=True)
            hash_by_course = {coursename : CourseDir(coursename).image_hash(proxy)
                              for coursename in coursenames}
        except Exception as e:
            logger.exception(
                "Cannot gather containers list at the docker daemon - skipping")
            return

        # a list of async futures
        futures = []
        for container in containers:
            try:
                name = container.name
                # too much spam ven in debug mode
                # logger.debug("dealing with container {}".format(name))
                coursename, student = name.split('-x-')
                figures_by_course.setdefault(coursename, CourseFigures())
                figures = figures_by_course[coursename]
                # may be None if s/t is misconfigured
                hash = hash_by_course[coursename] \
                       or "hash not found for course {}".format(coursename)
                monitored_jupyter = MonitoredJupyter(container, coursename, student, figures, hash)
                futures.append(monitored_jupyter.co_run(self.grace))
            # typically non-nbhosting containers
            except ValueError as e:
                # ignore this container as we don't even know
                # in what course it
                logger.info("ignoring non-nbhosting {}"
                            .format(container))
            except Exception as e:
                logger.exception("ignoring {} in monitor - unexpected exception"
                                 .format(container))
        # ds stands for disk_space
        docker_root = proxy.info()['DockerRootDir']
        nbhosting_root = sitesettings.root
        system_root = "/"
        ds = {}
        for name, root in ( ('docker', docker_root),
                            ('nbhosting', nbhosting_root),
                            ('system', system_root),
        ):
            ds[name] = {}
            try:
                stat = os.statvfs(root)
                ds[name]['percent'] = round(100 * stat.f_bfree / stat.f_blocks)
                # unit is MiB
                ds[name]['free'] = round((stat.f_bfree * stat.f_bsize) / (1024**2))
            
            except Exception as e:
                ds[name]['free'] = 0
                ds[name]['percent'] = 0
                logger.exception("monitor cannot compute disk space with name {} on {}"
                                 .format(name, root))

        # loads
        try:
            uptime_output = subprocess.check_output('uptime').decode().strip()
            end_of_line = uptime_output.split(':')[-1]
            floads = end_of_line.split(', ')
            load1, load5, load15 = [round(100*float(x)) for x in floads]

        except Exception as e:
            load1, load5, load15 = 0, 0, 0
            logger.exception("monitor cannot compute cpu loads")


        # run the whole stuff 
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(*futures))
        # write results
        for coursename, figures in figures_by_course.items():
            student_homes = CourseDir(coursename).student_homes()
            Stats(coursename).record_monitor_counts(
                figures.running_containers, figures.frozen_containers,
                figures.running_kernels,
                student_homes,
                load1, load5, load15,
                ds['docker']['percent'], ds['docker']['free'],
                ds['nbhosting']['percent'], ds['nbhosting']['free'],
                ds['system']['percent'], ds['system']['free'],
            )

    def run_forever(self):
        tick = time.time()

        # one cycle can take some time as all the jupyters need to be http-probed
        # so let us compute the actual time to wait
        logger.info("nbh-monitor is starting up")
        coursenames = CoursesDir().coursenames()
        for coursename in coursenames:
            Stats(coursename).record_monitor_known_counts_line()
        while True:
            try:
                self.run_once()
            # just be extra sure it doesn't crash
            except Exception as e:
                logger.exception("protecting against unexpected exception {}"
                                 .format(e))
            tick += self.period
            duration = max(0, int(tick - time.time()))
            logger.info("monitor is waiting for {}s".format(duration))
            time.sleep(duration)
