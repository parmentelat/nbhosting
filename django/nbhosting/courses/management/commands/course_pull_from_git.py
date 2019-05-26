# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_courses import CoursesDir
from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """update contents for course(s) from upstream git repo"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-a", "--all", action='store_true', default=False,
            help="redo all known courses")
        parser.add_argument("course", nargs="*")

    def handle(self, *args, **kwargs):
        courses = kwargs['course']
        if not courses:
            if kwargs['all']:
                courses = CoursesDir().coursenames()
            else:
                print("must provide at least one course, or --all")
                exit(1)
        for course in courses:
            coursedir = CourseDir(course)
            if not coursedir.is_valid():
                logger.error(f"no such course {course}")
                return
            logger.info(f"{40*'='} pulling from git for {course}")
            coursedir.pull_from_git()
