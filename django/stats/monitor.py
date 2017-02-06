#!/usr/bin/env python3

import os
import os.path
import time
import argparse

import docker

from nbhosting.settings import nbhosting_settings
from nbhosting.settings import logger
from stats import Stats

"""
This processor is designed to be cron'ed
It will spot and kill jupyter instances that have had no recent activity

* the notion of 'recent' activity is basic
  as of this first rough implem, nbh-run-student-course-jupyter touches a file
  named .monitor at the root of the jupyter space, and this is used as an indication 
  of the last activity
  jupyter flaks said that in v5 there will be some api to deal with that

* when an instance is killed, the stats/<course/events.raw file
  is also updated with a 'killing' line
"""

class CourseFigures:
    def __init__(self):
        self.frozen = 0
        self.running = 0
    def count_container(self, running: bool):
        if running:
            self.running +=1
        else:
            self.frozen += 1

def monitor(grace: int):
    """
    grace is expressed in minutes
    """

    now = time.time()
    grace_seconds = grace*60
    grace_past = now - grace_seconds

    root = nbhosting_settings['root']
    try:
        proxy = docker.from_env()
        containers = proxy.containers.list(all=True)
    except Exception as e:
        logger.exception("Cannot gather containers list at the docker daemon - skipping")
        return

    figures_per_course = {}
    
    for container in containers:
        logger.info("monitoring containers")
        try:
            name = container.name
            course, student = name.split('-x-')
            figures_per_course.setdefault(course, CourseFigures())
            # stopped containers are useful only for statistics
            if container.status != 'running':
                figures_per_course[course].count_container(False)
                continue
            stamp = os.path.join(root, "students", student, course, ".monitor")
            mtime = os.stat(stamp).st_mtime
            if mtime > grace_past:
                logger.debug("sparing {} that had activity {}' ago"
                             .format(name, (now-mtime)//60))
                figures_per_course[course].count_container(True)
                continue
            logger.info("Killing container {}".format(name))
            # not sure what signal would be best ?
            container.kill()
            figures_per_course[course].count_container(False)
            Stats(course).record_kill_jupyter(student)

        except FileNotFoundError as e:
            logger.info("container {} has no .monitor stamp - ignoring"
                        .format(name))
            figures_per_course[course].count_container(container.status == 'running')
        # typically non-nbhosting continers
        except ValueError as e:
            logger.info("ignoring non-nbhosting container {}"
                        .format(name))
            # cannot count this one as we don't eveb know in what course it is
    for course, figures in figures_per_course.items():
        Stats(course).record_jupyters_count(figures.running, figures.frozen)
        
def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # default is 2 hours
    parser.add_argument("-g", "--grace", default=2*60, type=int,
                        help="grace timeout in minutes")
    parser.add_argument("-p", "--period", default=15, type=int,
                        help="monitor period in minutes - how often are checked done")
    args = parser.parse_args()
    while True:
        monitor(args.grace)
        time.sleep(60*args.period)
    

if __name__ == '__main__':
    main()
