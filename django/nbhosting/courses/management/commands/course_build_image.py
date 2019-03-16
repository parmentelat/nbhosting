# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_courses import CoursesDir
from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """rebuild docker image for that course

    NOTE that courses that override
    their image so as to use another course's
    image are not allowed to rebuild"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--force", action='store_true', default=False,
            help="""when set, this option causes build to be forced;
            that is to say, docker build is invoked with the --no-cache option.
            Of course this means a longer execution time""")
        parser.add_argument(
            "-a", "--all", action='store_true', default=False,
            help="redo all known courses")
        parser.add_argument("course", nargs="*")

    def handle(self, *args, **kwargs):
        force = kwargs['force']

        courses = kwargs['course']
        if not courses:
            if kwargs['all']:
                courses = CoursesDir().coursenames()
            else:
                parser.print_help()
                exit(1)
        for course in courses:
            coursedir = CourseDir(course)
            if not coursedir.is_valid():
                logger.error(f"no such course {course}")
                return
            coursedir.build_image(force)
            logger.info(f"{40*'='} building image for {course}")
            coursedir.build_image(force)
