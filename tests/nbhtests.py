#!/usr/bin/env python3

"""
Utility to open a large number of notebooks 

We use subprocess because phantom and selenium are not asyncio-friendly,
and there is no clear advantage in running all the open-notebook instances
in a single process, so let's keep it simple
"""

import time
import subprocess
import random
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from intsranges import IntsRanges

from nbhtest import list_notebooks, default_course_gitdir, default_topurl
   

def main() -> bool:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-U", "--url", default=default_topurl,
                        dest='topurl',
                        help="url to reach nbhosting server")
    parser.add_argument("-c", "--course-gitdir", default=default_course_gitdir,
                        help="""location of a git repo where to fetch notebooks;
                                needed in order to generate relevant URLs""")
    parser.add_argument("-i", "--indices", default=[0], action=IntsRanges,
                        help="(cumulative) ranges of indices in the list of known notebooks"
                        " - run nbhtest with -l to see list")
    parser.add_argument("-u", "--users", default=[1], action=IntsRanges,
                        help="(cumulative) ranges of students indexes; e.g. -u 101-400 -u 501-600")
    parser.add_argument("-m", "--random", action='store_true',
                        help="if set, a random notebook index is used for each student")
    parser.add_argument("-b", "--base", default='student',
                        help="basename for students name")
    parser.add_argument("-p", "--period", default=20, type=float,
                        help="delay between 2 triggers of nbhtest")
    parser.add_argument("-s", "--sleep", default=3, type=int,
                        help="delay in seconds to sleep between actions inside nbhtest")
    parser.add_argument("-n", "--dry-run", action='store_true')
    args = parser.parse_args()

    course_gitdir = args.course_gitdir
    course, notebooks = list_notebooks(course_gitdir)
    
    # in random mode; what are the choices that we randomize on
    if args.random:
        if len(args.indices) > 1:
            choices = args.indices
        else:
            choices = list(range(len(notebooks)))

    overall = True
    for user in args.users:
        student_name = "{}-{:04d}".format(args.base, user)
        if args.random:
            indices = [ random.choice(choices) ]
        else:
            indices = args.indices
        for index in indices:
            command = "nbhtest.py -U {} -c {} -i {} -u {} -s {} &"\
                      .format(args.topurl, course_gitdir, index, student_name, args.sleep)
            if args.dry_run:
                print("dry-run:", command)
            else:
                print("Running command:", command)
                if subprocess.call(command, shell=True) != 0:
                    overall = False
                time.sleep(args.period)
    return overall


if __name__ == '__main__':
    exit(0 if main() else 1)
