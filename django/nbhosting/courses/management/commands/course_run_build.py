# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    run a build as defined in nbhosting.YAML, in a separate container
    """


    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry-run", action='store_true', default=False,
            help="simply show what would be done")
        parser.add_argument("coursename", type=str)
        parser.add_argument("build_patterns", type=str, nargs='*',
                            help="patterns that describe the builds to run "
                                 "default is to build all known builds")


    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        coursename = kwargs['coursename']
        build_patterns = kwargs['build_patterns']
        coursedir = CourseDir.objects.get(coursename=coursename)
        coursedir.run_extra_builds(build_patterns, dry_run=dry_run)