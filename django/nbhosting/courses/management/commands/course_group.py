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
        parser.add_argument("-r", "--remove", default=False, action='store_true')
        parser.add_argument("-l", "--list", default=False, action='store_true',
                            help="display groups after operation is complete."
                                 "defaults to true if no group is given")
        parser.add_argument("coursename")
        parser.add_argument("groupname", nargs='*')

    def handle(self, *args, **kwargs):

        remove = kwargs['remove']
        coursename = kwargs['coursename']
        groupnames = kwargs['groupname']
        list_flag = kwargs['list'] or not groupnames

        try:
            course = CourseDir.objects.get(coursename=coursename)
        except CourseDir.DoesNotExist:
            logger.error(f"course {coursename} not found")
            exit(1)

        def describe():
            if not list_flag:
                return
            groups = ('+'.join(g.name
                               for g in course.registered_groups.iterator()))
            print(f"{coursename}: [{groups}]")

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
