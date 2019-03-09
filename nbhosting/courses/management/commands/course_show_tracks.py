# pylint: disable=c0111, r0201, w0613

from pathlib import Path

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

class Command(BaseCommand):
    help = 'Display static mappings for a course'

    def add_arguments(self, parser):
        parser.add_argument(
            "-p", "--preserve-cache", dest='preserve', default=False,
            action='store_true',
            help="preserve cached tracks, which by default are cleared")
        parser.add_argument("coursename")

    def handle(self, *args, **kwargs):
        preserve = kwargs['preserve']
        coursename = kwargs['coursename']
        coursedir = CourseDir(coursename)
        if not preserve:
            caches = (coursedir.notebooks_dir / ".tracks").glob("*.json")
            for cache in caches:
                print(f"clearing cache {cache}")
                cache.unlink()
        tracks = coursedir.tracks()
        for trackname in tracks:
            print(f"{trackname}: {coursedir.track(trackname)}")
