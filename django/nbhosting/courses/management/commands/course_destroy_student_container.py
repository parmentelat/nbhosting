# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_courses import CoursesDir
from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    for a given student, kill if needed, and rm if needed,
    its container for that course
    """

    def add_arguments(self, parser):
#        parser.add_argument(
#            "-a", "--all", action='store_true', default=False,
#            help="apply to all students")
        parser.add_argument("course", nargs=1, type=str)
        parser.add_argument("student", nargs="+")

    def handle(self, *args, **kwargs):

        course = kwargs['course'][0]
        students = kwargs['student']
        coursedir = CourseDir(course)
        if not coursedir.is_valid():
            logger.error(f"no such course {course}")
            return

        for student in students:
            coursedir.destroy_student_container(student)
