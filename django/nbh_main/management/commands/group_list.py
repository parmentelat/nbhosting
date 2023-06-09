# pylint: disable = c0111, w1203

"""
a utility command to list users in groups
"""

from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group

from nbhosting.matching import matching_policy

def iter_len(iter):
    return sum(1 for _ in iter)

def list_groups_users(patterns, verbose):
    """
    see verbosity meaning below
    """
    for group in Group.objects.all():
        if not matching_policy(group.name, patterns):
            continue
        if not verbose:
            print(group.name)
            continue
        users = group.user_set.all()
        if verbose == 1:
            print(f"{group.name} has {iter_len(users)} user(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {group.name} has {iter_len(users)} user(s)")
        for user in users:
            print(user.username)


def list_groups_courses(patterns, verbose):
    """
    see verbosity meaning below
    """
    for group in Group.objects.all():
        if not matching_policy(group.name, patterns):
            continue
        if not verbose:
            print(group.name)
            continue
        courses = group.courses_registered.all()
        if verbose == 1:
            print(f"{group.name} is in {iter_len(courses)} course(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {group.name} is in {iter_len(courses)} course(s)")
        for course in courses:
            print(course.coursename)


class Command(BaseCommand):

    help = """%(prog)s : displays groups;

    2 modes are available, to inspect either users (default)
    or related courses (option -c);

    patterns are matched using usual nbh matching policy, i.e.

    (*) plain string matches if group name contains that string
    (*) otherwise '*' in a pattern is a wildcard;

    verbosity is used like this (same with courses if -c is selected)
      verbose=0: only group names;
      verbose=1: + number of students;
      verbose=2: only list of students;
      verbose=3: number of students + list of students
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--list", action="count", default=0,
            dest="verbose",
            help=("Give more output. "
                  "Option is additive, and can be used up to 3 times."),
        )
        parser.add_argument(
            "-c", "--courses", default=False, action="store_true",
            help="list related courses instead of related users",
        )
        parser.add_argument(
            "pattern", nargs='*',
            help="group patterns")

    def handle(self, *args, **kwargs):
        patterns = kwargs['pattern']
        courses_mode = kwargs['courses']
        verbose = kwargs['verbose']
        if not patterns:
            patterns = ['*']
        if courses_mode:
            list_groups_courses(patterns, verbose)
        else:
            list_groups_users(patterns, verbose)
