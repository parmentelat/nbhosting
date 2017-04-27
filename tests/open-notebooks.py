#!/usr/bin/env python3

"""
Utility to open a large number of notebooks 

We use subprocess because phantom and selenium are not asyncio-friendly,
and there is no clear advantage in running all the open-notebook instances
in a single process, so let's keep it simple
"""

import time
import subprocess
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from intsranges import IntsRanges


def main() -> bool:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--range", action=IntsRanges,
                        default=[1],
                        help="(cumulative) ranges of students indexes")
    parser.add_argument("-b", "--base", default='student',
                        help="basename for students name")
    parser.add_argument("-d", "--delay", default=3, type=float,
                        help="delay between 2 triggers of open-notebook")
    parser.add_argument("-i", "--index", default=0, type=int,
                        help="index in the list of known notebooks - run open-notebook with -l to see list")
    parser.add_argument("-s", "--sleep", default=3, type=int,
                        help="delay in seconds to sleep between actions")
    args = parser.parse_args()
    overall = True
    for n in args.range:
        student_name = "{}-{:04d}".format(args.base, n)
        command = "open-notebook.py -i {} -u {} -s {} &"\
                  .format(args.index, student_name, args.sleep)
        print("Running command:", command)
        subprocess.call(command, shell=True)
        time.sleep(args.sleep)

if __name__ == '__main__':
    exit(0 if main() else 1)
    
    
                        
    
