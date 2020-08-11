# pylint: disable = c0111, w1203

"""
a utility command to list users in groups
"""

from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group

from nbhosting.matching import matching_policy

def iter_len(iter):
    return sum(1 for _ in iter)
    
def list_groups(patterns, verbose):
    """
    verbose=0: only group names
    verbose=1: + number of students
    verbose=2: all usernames
    """
    for group in Group.objects.all():
        if not matching_policy(group.name, patterns):
            continue
        if not verbose:
            print(group.name)
            continue
        if verbose == 1:
            print(f"{group.name} has {iter_len(group.user_set.all())} users")
            continue
        print(f"{10*'-'} {group.name} has {iter_len(group.user_set.all())} users")
        for user in group.user_set.all():
            print(user.username)


class Command(BaseCommand):

    help = """%(prog)s : displays groups and contents

    patterns are matched using usual nbh matching policy, i.e.
    
    (*) plain string matches if group name contains that string
    (*) otherwise '*' in a pattern is a wildcard

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--list", action="count", default=0,
            dest="verbose",
            help=("Give more output. Option is additive, and can be used up to 2 "
                  "times."),
        )   
        parser.add_argument(
            "pattern", nargs='*', 
            help="group patterns")

    def handle(self, *args, **kwargs):
        patterns = kwargs['pattern']
        if not patterns:
            patterns = ['*']
        list_groups(patterns,
                    kwargs['verbose'])