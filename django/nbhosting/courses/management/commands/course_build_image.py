# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """rebuild docker image for that course

    NOTE that courses that override
    their image so as to use another course's
    image are not allowed to rebuild"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--force", action='store_true', default=False,
            help="""when set, this option causes build to be forced;
            that is to say, docker build is invoked with the --no-cache option.
            Of course this means a longer execution time""")
        parser.add_argument("course")

    def handle(self, *args, **kwargs):
        force = kwargs['force']
        force_tag = "" if not force else "--no-cache"
        course = kwargs['course']

        coursedir = CourseDir(course)
        if not coursedir.is_valid():
            logger.error(f"no such course {course}")
            exit(1)
        build_dir = coursedir.build_dir

        image = coursedir.image
        if image != coursedir.coursename:
            logger.error(
                f"cowardly refusing to rebuild image {image}"
                f" from course {coursedir.coursename}\n"
                f"the 2 names should match")
            exit(1)

        dockerfile = coursedir.customized("Dockerfile")
        if not dockerfile or not dockerfile.exists():
            logger.error(f"Could not spot Dockerfile for course {course}")
            exit(1)

        def show_and_run(command):
            logger.info(f"# {command}")
            os.system(command)

        # clean up and repopulate build dir
        show_and_run(f"rm -rf {build_dir}/*")
        build_dir.exists() or build_dir.mkdir()

        show_and_run(f"cp {dockerfile} {build_dir}/Dockerfile")
        show_and_run(f"cp {NBHROOT}/images/start-in-dir-as-uid.sh {build_dir}")
        show_and_run(f"cd {build_dir}; "
                     f"docker build {force_tag} -f Dockerfile -t {image} .")
