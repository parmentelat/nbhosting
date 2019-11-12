#!/usr/bin/env python3

"""
Utility to open a large number of notebooks 

We use subprocess because phantom and selenium are not asyncio-friendly,
and there is no clear advantage in running all the open-notebook instances
in a single process, so let's keep it simple
"""

import time
import random
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from intsranges import IntsRanges

import asyncio
from asynciojobs import Scheduler
from apssh import LocalNode, SshJob
from apssh.formatters import TerminalFormatter

from nbhtest import (
    default_course_gitdir, 
    default_topurl,
    default_sleep_internal,
    Contents,
    )
   
default_window = 5

def main() -> bool:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-U", "--url", default=default_topurl,
                        dest='topurl',
                        help="url to reach nbhosting server")
    parser.add_argument("-i", "--indices", default=[0], action=IntsRanges,
                        help="(cumulative) ranges of indices in the list of known notebooks"
                        " - run nbhtest with -l to see list")
    parser.add_argument("-u", "--users", default=[1], action=IntsRanges,
                        help="(cumulative) ranges of students indexes; e.g. -u 101-400 -u 501-600")
    parser.add_argument("-b", "--base", default='student',
                        help="basename for students name")
    parser.add_argument("-p", "--period", default=20, type=float,
                        help="delay between 2 triggers of nbhtest")
    parser.add_argument("-s", "--sleep", default=default_sleep_internal, type=float,
                        help="delay in seconds to sleep between actions inside nbhtest")
    parser.add_argument("-w", "--window", default=default_window, type=int,
                        help="window depth for spawning the nbhtest instances")
    parser.add_argument("-n", "--dry-run", action='store_true')
    parser.add_argument("coursedirs", default=[default_course_gitdir],
                        nargs='*',
                        help="""a list of git repos where to fetch notebooks""")
    
    args = parser.parse_args()
    print(args.coursedirs)

    local = LocalNode(
        formatter=TerminalFormatter(
            custom_format="%H-%M-%S:@line@",
            verbose=True
            ))

    scheduler = Scheduler()

    for user in args.users:
        student_name = f"{args.base}-{user:04d}"
        for index in args.indices:
            command = (f"nbhtest.py -U {args.topurl} -u {student_name} "
                       f"-s {args.sleep} ")
            for coursedir in args.coursedirs:
                command += f"{coursedir}:{index} "
            command += " &"
            if args.dry_run:
                print("dry-run:", command)
            else:
                # schule this command to run
                job = SshJob(
                    scheduler=scheduler,
                    node=local,
                    commands = [command, f"sleep {args.period}"])
                
    if args.dry_run:
        return True

    scheduler.jobs_window = args.window
    overall = scheduler.orchestrate()
    if not overall:
        scheduler.debrief()
    print("nbhtests DONE")
    return overall


if __name__ == '__main__':
    exit(0 if main() else 1)
