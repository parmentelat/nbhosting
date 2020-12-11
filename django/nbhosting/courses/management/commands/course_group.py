# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir
from django.contrib.auth.models import User, Group

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command adds groups to a course
    unless -r is provided, 
    in which case it removes them
    """

    def add_arguments(self, parser):
        parser.add_argument("-r", "--remove", default=False)
        parser.add_argument("-v", "--verbose", default=False)
        parser.add_argument("coursename")
        parser.add_argument("groupname", nargs='+')

    def handle(self, *args, **kwargs):

        verbose = kwargs['verbose']
        remove = kwargs['remove']
        oldname = kwargs['oldname']
        groupnames = kwargs['groupnames']

        try:
            course = CourseDir.objects.get(coursename=oldname)
        except CourseDir.DoesNotExist:
            logger.error(f"course {oldname} not found")
            exit(1)

        def describe():
            if not verbose:
                return
            print(f"{coursename}: "
                  f"[{'+'.join(g for g in course.registered_groups.iterator())}]")

        for groupname in groupnames:
            try:
                group = Group.objects.get(name=groupname)
            except NameError:
                logger.error(f"group {groupname} not found - ignored")
                break
            if not remove:
                course.registered_groups.add(group)
            else:
                course.registered_groups.remove(group)
        else:
            describe()
            # all groups were found : OK
            return 0
        describe()
        return 1
