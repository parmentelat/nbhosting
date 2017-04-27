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


def main() -> bool:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--ranges", default=[1], action=IntsRanges,
                        help="(cumulative) ranges of students indexes")
    parser.add_argument("-i", "--indices", default=[0], action=IntsRanges,
                        help="(cumulative) ranges of indices in the list of known notebooks"
                        " - run open-notebook with -l to see list")
    parser.add_argument("-m", "--random", action='store_true',
                        help="if set, a random notebook index is used for each student")
    parser.add_argument("-b", "--base", default='student',
                        help="basename for students name")
    parser.add_argument("-d", "--delay", default=3, type=float,
                        help="delay between 2 triggers of open-notebook")
    parser.add_argument("-s", "--sleep", default=3, type=int,
                        help="delay in seconds to sleep between actions inside open-notebook")
    parser.add_argument("-n", "--dry-run", action='store_true')
    args = parser.parse_args()

    if args.random:
        if len(args.indices) > 1:
            choices = args.indices
        else:
            from nbhtest import list_bioinfo_notebooks
            choices = list(range(len(list_bioinfo_notebooks())))

    overall = True
    for n in args.ranges:
        student_name = "{}-{:04d}".format(args.base, n)
        if args.random:
            indices = [ random.choice(choices) ]
        else:
            indices = args.indices
        for index in indices:
            command = "nbhtest.py -i {} -u {} -s {} &"\
                      .format(index, student_name, args.sleep)
            if args.dry_run:
                print("dry-run:", command)
            else:
                print("Running command:", command)
                if subprocess.call(command, shell=True) != 0:
                    overall = False
                time.sleep(args.sleep)
    return overall

if __name__ == '__main__':
    exit(0 if main() else 1)
    
    
                        
    
