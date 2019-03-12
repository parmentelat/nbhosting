# pylint: disable=c0111, r0201, w0613

from pathlib import Path

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger

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
        logger.info(f"preserve mode = {preserve}")
        if not preserve:
            cache = (coursedir.notebooks_dir / ".tracks.json")
            if cache.exists():
                logger.info(f"clearing cache {cache}")
                cache.unlink()
        tracks = coursedir.tracks()
        for track in tracks:
            logger.info(f"{track.name}: {track}")
            for section in track.sections:
                logger.info(f"{4*' '}{section.name}")
                for notebook in section.notebooks:
                    logger.info(f"{8*' '}{notebook.notebookname}")
