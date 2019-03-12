# pylint: disable=c0111, r0201, w0613

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir
from nbhosting.courses.model_mapping import StaticMapping

class Command(BaseCommand):
    help = 'Display all toplevel dirs involved in at least one static mapping for a course'

    def add_arguments(self, parser):
        parser.add_argument("coursename")

    def handle(self, *args, **kwargs):
        coursename = kwargs['coursename']
        coursedir = CourseDir(coursename)
        toplevels = StaticMapping.static_toplevels(
            coursedir.static_mappings
        )
        for toplevel in toplevels:
            print(toplevel)
