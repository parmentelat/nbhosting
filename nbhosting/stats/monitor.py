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

* the notion of 'recent' activity takes advantage of a feature
  introduced in jupyter5, where the /api/kernels/ call returns for
  each kernel its last activity

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

    def last_time(self, kernel_data):
        """
        expects as input the data returned by /api/kernels
        for one kernel, that is to say e.g.:
        {'connections': 1,
         'execution_state': 'idle',
         'id': '15be5b4c-b5f2-46f0-9a9b-ff54f4495cb4',
         'last_activity': '2018-02-19T12:58:25.204761Z',
         'name': 'python3'}

        returns a comparable time (using max) that this kernel
        has been doing something
        
        Notes:
        * cases where connections = 0 should not be disregarded
          it is important to keep those alive, it does not indicate
          a lack of activity
        * last_activity format: we found some items where the milliseconds
          part was simply not present (at all, i.e. not exposed as .0 or anything)
        * if anything goes wrong, it's best to return a timestamp that means 'now'
          rather than the epoch
        """
        try:
            last = kernel_data['last_activity']
            # normalize
            last = last.replace('Z', 'UTC')
            struct_time = None
            # try 2 formats
            try:
                struct_time = time.strptime(last, "%Y-%m-%dT%H:%M:%S.%f%Z")
            except:
                struct_time = time.strptime(last, "%Y-%m-%dT%H:%M:%S%Z")
            return calendar.timegm(struct_time)
        except Exception as e:
            logger.error(f"MonitoredJupyter.last_time - fatal error {type(e)} - {e}")
            return time.time()

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

            last_times = [
                self.last_time(api_kernel) for api_kernel in api_kernels
            ]
            # if times is empty (no kernel): no activity
            self.last_activity = max(last_times, default=0)
                
        except Exception as e:
            logger.exception("Cannot probe number of kernels in {} - {}: {}"
                             .format(self, type(e), e))
            self.last_activity = None


    async def co_run(self, grace):
        nbhroot = Path(sitesettings.nbhroot)
        # stopped containers are useful only for statistics
        if self.container.status != 'running':
            self.figures.count_container(False)
            return
        # count number of kernels and last activity
        await self.count_running_kernels()
        # last_activity may be 0 if no kernel is running inside that container
        # or None if we could not determine it properly
        if self.last_activity is None:
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
            if self.last_activity:
                logger.info("{} has been idle for {} mn - killing".format(self, idle_minutes))
            else:
                logger.info("{} has no kernel attached - killing".format(self))
            # kill it
            self.container.kill()
            # if that container does not run the expected image hash
            # it is because the course image was upgraded in the meanwhile
            # then we even remove the container so it will get re-created
            # next time with the right image this time
            actual_hash = self.container.image.id
            if actual_hash != self.hash:
                logger.info("removing container {} - has hash {} instead of expected {}"
                            .format(self.name, actual_hash[:15], self.hash[:15]))
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
        nbhroot = sitesettings.nbhroot
        system_root = "/"
        ds = {}
        for name, root in ( ('docker', docker_root),
                            ('nbhosting', nbhroot),
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
