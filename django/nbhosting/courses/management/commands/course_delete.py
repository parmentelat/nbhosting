# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command lets you delete a course 

    by default, all the students local spaces pertaining to that course
    are deleted as well, unless you provide the --preserve-students flag
    
    by default, the raw/ area that has logs of the activity is preserved,
    unless you provide the --clean-raw flag
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-p", "--preserve-students", action='store_true', default=False,
            help="preserve student spaces")
        parser.add_argument(
            "-c", "--clean-raw", action='store_true', default=False,
            help="clean the raw/ area with logs of activity")
        parser.add_argument("coursename")

    def handle(self, *args, **kwargs):

        coursename = kwargs['coursename']
        preserve_students = kwargs['preserve_students']
        clean_raw = kwargs['clean_raw']

        try:
            already = CourseDir.objects.get(coursename=coursename)
            already.clean_before_delete(preserve_students=preserve_students,
                                        clean_raw=clean_raw)
            # remove from database
            already.delete()
            return 0
        except CourseDir.DoesNotExist:
            logger.error(f"course {coursename} not found")
            exit(1)
