# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_courses import CoursesDir
from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command lets you create a course from a git repo

    by default, the coursename is used as the docker image name, but you can use the -i option to declare that you'd prefer to use another image instead
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

        try:
            coursedir = CourseDir(coursename)
            if coursedir.is_valid():
                print(f"course {coursename} already existing")
                exit(1)
        except:
            pass
        coursedir.run_nbh_subprocess('course-init', git_url)
        # reload now that it's created
        coursedir = CourseDir(coursename)
        coursedir.pull_from_git()
        # set image
        image = kwargs['image'] or coursename
        coursedir.set_image(image)
        return 0
