# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    rebuild container image for selected courses

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
        parser.add_argument("patterns", nargs='*', type=str)


    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        force = kwargs['force']

        patterns = kwargs['patterns']
        selected = sorted(CourseDir.courses_by_patterns(patterns))
        for coursedir in selected:
            logger.info(f"{40*'='} building image for {coursedir.coursename}")
            coursedir.build_image(force, dry_run)
