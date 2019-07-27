# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command lets you rename an existing course 
    """

    def add_arguments(self, parser):
        parser.add_argument("oldname")
        parser.add_argument("newname")

    def handle(self, *args, **kwargs):

        oldname = kwargs['oldname']
        newname = kwargs['newname']

        try:
            instance = CourseDir.objects.get(coursename=oldname)
            try:
                should_not_exist = CourseDir.objects.get(coursename=newname)
                logger.error(f"course {newname} already exists")
                exit(1)
            except CourseDir.DoesNotExist:
                pass
        except CourseDir.DoesNotExist:
            logger.error(f"course {oldname} not found")
            exit(1)

        instance.run_nbh_subprocess("course-rename", newname)
        instance.coursename = newname
        instance.save()
        return 0
