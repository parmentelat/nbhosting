# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    for a given student, kill if needed, and rm if needed,
    its container for that course
    """

    def add_arguments(self, parser):
        parser.add_argument("course", nargs=1, type=str)
        parser.add_argument("student", nargs="+")

    def handle(self, *args, **kwargs):

        coursename = kwargs['course'][0]
        students = kwargs['student']
        try:
            coursedir = CourseDir.objects.get(coursename=coursename)
            for student in students:
                coursedir.destroy_student_container(student)
        except CourseDir.DoesNotExist:
            logger.error(f"no such course {coursename}")
            return

