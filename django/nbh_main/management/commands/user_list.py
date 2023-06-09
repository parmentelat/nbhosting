# pylint: disable = c0111, w1203

"""
a utility command to list users and their groups
"""

from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group

from nbhosting.matching import matching_policy

def iter_len(iter):
    return sum(1 for _ in iter)

def list_users(patterns, verbose):
    """
    see verbosity meaning below
    """
    for user in User.objects.all():
        if not matching_policy(user.username, patterns):
            continue
        if not verbose:
            print(user.username)
            continue
        groups = user.groups.all()
        if verbose == 1:
            print(f"{user.username} is in {iter_len(groups)} group(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {user.username} is in {iter_len(groups)} group(s)")
        for group in groups:
            print(group.name)


class Command(BaseCommand):

    help = """%(prog)s : displays users and their groups;

    patterns are matched using usual nbh matching policy, i.e.

    (*) plain string matches if user name contains that string
    (*) otherwise '*' in a pattern is a wildcard
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--list", action="count", default=0,
            dest="verbose",
            help=("Give more output. "
                  "Option is additive, and can be used up to 3 times."),
        )
        parser.add_argument(
            "pattern", nargs='*',
            help="group patterns")

    def handle(self, *args, **kwargs):
        patterns = kwargs['pattern']
        verbose = kwargs['verbose']
        if not patterns:
            patterns = ['*']
        list_users(patterns, verbose)
