# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command is designed to be run cyclically with cron or systemd

    it performs course-update-from-git
    on all courses that have their autopull setting defined as true
    """


    def add_arguments(self, parser):
        parser.add_argument(
            "-a", "--all", action='store_true', default=False,
            help="apply to all known courses")
        parser.add_argument("coursenames", nargs="*")


    def handle(self, *args, **kwargs):

        coursenames = kwargs['coursenames']
        if not coursenames:
            if kwargs['all']:
                coursenames = sorted(
                    (cd.coursename for cd in CourseDir.objects.all()))
            else:
                print("must provide at least one course, or --all")
                exit(1)
        for coursename in coursenames:
            coursedir = CourseDir.objects.get(coursename=coursename)
            if not coursedir.is_valid():
                logger.error(f"no such course {coursename}")
                continue
            if not coursedir.autopull:
                logger.info(f"course {coursename} has not opted for autopull")
                continue
            logger.info(f"{40*'='} pulling from git with course {coursename}")
            coursedir.pull_from_git()
            # xxx we may need some exclusion mechanism to avoid
            # having 2 builds running simultaneously
            if coursedir.autobuild:
                logger.info(f"autobuild: rebuilding {coursedir.coursename}")
                coursedir.run_builds('*')
