# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command lets you create a course from a git repo

    by default, the coursename is used as the container image name, 
    but you can use the -i option to declare that you'd prefer to use another image instead
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-i", "--image", action='store', default=None,
            help="specify an alternate image name")
        parser.add_argument("coursename")
        parser.add_argument("git_url")

    def handle(self, *args, **kwargs):

        coursename = kwargs['coursename']
        git_url = kwargs['git_url']
        image = kwargs['image']

        try:
            already = CourseDir.objects.get(coursename=coursename)
            logger.error(f"course {coursename} already existing")
            exit(1)
        except CourseDir.DoesNotExist:
            kwds = {}
            kwds['image'] = image if image else coursename
            created = CourseDir.objects.create(
                coursename=coursename, giturl=git_url, **kwds)
            ok = (created.run_nbh_subprocess('course-init', git_url)
                  and created.pull_from_git())
            if not ok:
                logger.error(f"Could not create course {coursename}")
                logger.warning(f"Double-check (remove if exists) git repo {created.git_dir}")
                created.delete()
            return 0
