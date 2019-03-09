# pylint: disable=c0111, r0201, w0613

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

class Command(BaseCommand):
    help = 'Display static mappings for a course'

    def add_arguments(self, parser):
        parser.add_argument("coursename")

    def handle(self, *args, **kwargs):
        coursename = kwargs['coursename']
        coursedir = CourseDir(coursename)
        for static_mapping in coursedir.static_mappings:
            print(static_mapping.expose(coursedir))
