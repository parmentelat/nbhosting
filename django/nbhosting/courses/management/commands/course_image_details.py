# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    display details about the course images
    """


    def add_arguments(self, parser):
        parser.add_argument("patterns", nargs='*', type=str)


    def handle(self, *args, **kwargs):
        patterns = kwargs['patterns']
        selected = sorted(CourseDir.courses_by_patterns(patterns))
        for coursedir in selected:
            logger.info(f"{40*'='} image details for {coursedir.coursename}")
            coursedir.run_image_details()
