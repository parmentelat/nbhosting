# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    rebuild container image for that course

    NOTE that courses that override
    their image so as to use another course's
    image are not allowed to rebuild
    """


    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry-run", action='store_true', default=False,
            help="simply show what would be done")
        parser.add_argument(
            "-f", "--force", action='store_true', default=False,
            help="""when set, this option causes build to be forced;
            that is to say, podman build is invoked with the --no-cache option.
            Of course this means a longer execution time""")
        parser.add_argument(
            "-a", "--all", action='store_true', default=False,
            help="redo all known courses")
        parser.add_argument("coursenames", nargs="*")


    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        force = kwargs['force']

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
                return
            logger.info(f"{40*'='} building image for {coursename}")
            coursedir.build_image(force, dry_run)
