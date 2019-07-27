# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command list known courses
    
    without argument it lists all courses; with arguments
    it lists all course whose name contains any of the tokens
    
    example: nbh-manage courses-list python bio
    
    could output: bioinfo mines-python-primer 
    python-slides python3-s2 
    """

    def add_arguments(self, parser):
        parser.add_argument("patterns", nargs='*', type=str)

    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']

        all_coursedirs = sorted(
            CourseDir.objects.all(),
            key=lambda coursedir: coursedir.coursename)
        for coursedir in all_coursedirs:
            name = coursedir.coursename
            if not patterns:
                print(name)
            else:
                for pattern in patterns:
                    if pattern in name:
                        print(name)
                        break
        return 0
