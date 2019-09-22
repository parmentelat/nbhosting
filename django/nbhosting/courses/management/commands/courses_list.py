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
        parser.add_argument("-l", "--long", action='store_true', default=False,
                            help="show more info")

    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']
        long = kwargs['long']

        def show_course(cd):
            if not long:
                print(cd.coursename)
            else:
                autopull = "on" if cd.autopull else "off"
                hash = cd.current_hash()
                print(f"{cd.coursename:20s}\t{cd.image:30s}[AP {autopull:3s}]\t{hash}\t{cd.giturl}")

        all_coursedirs = sorted(
            CourseDir.objects.all(),
            key=lambda coursedir: coursedir.coursename)
        for coursedir in all_coursedirs:
            name = coursedir.coursename
            if not patterns:
                show_course(coursedir)
            else:
                for pattern in patterns:
                    if pattern == '*' or pattern in name:
                        show_course(coursedir)
                        break
        return 0
