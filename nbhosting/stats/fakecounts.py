#!/usr/bin/env python3
import random
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

"""
This code produces random data for testing the stats view
of course it is not meant to run in production
"""

from nbhosting.stats.stats import Stats

def random_range(a, b):
    return a + (b-a)*random.random() 

def fake_counts(course, period, nb_students, delta , days, beg=None):

    """
    period is in minutes
    delta is the max difference between 2 points
    """

    stats = Stats(course)
    path = stats.monitor_counts_path()
    # make sure the file is void
    can_open = False
    try:
        with path.open() as f:
            can_open = f.read()
    except:
        pass

    if can_open:
        print("wow wow wow: file={}".format(path))
        print("cowardly refusing to create events in non-empty file - clear first")
        exit(1)
    
    nb_students = int(nb_students)

    if beg is None:
        beg = time.time()
    beg = int(beg)
    end = beg + days * 24 * 3600

    print("Generating fake counts for course {}".format(course))
    print("with {} students".format(nb_students))
    print("every {} minutes over {} days".format(period, days))
    print("starting {}".format(
        time.strftime(Stats.time_format, time.localtime(beg))))

    pointer = beg
    total, running, kernels = 0, 0, 0
    
    while pointer <= end:
        frozen = total - running
        timestamp = time.strftime(Stats.time_format, time.localtime(pointer))
        # can't fake number students in line with the other source 
        stats.record_monitor_counts(running, frozen, kernels, timestamp, 0)

        news = random.randint(0, delta)
        total = min(nb_students, total+news)
        running = running + random.randint(-delta, delta)
        running = max(running, 0)
        running = min(total, running)
        kernels = int(running * random_range(2., 10.))
        pointer += period*60

    print("(Over)wrote {}".format(stats.monitor_counts_path()))


# pass course name as sys.argv[1] with optional args
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--period", type=int, default=10, help="in minutes")
parser.add_argument("-s", "--students", type=int, default=4000, help="number of students")
parser.add_argument("-D", "--delta", type=int, default=8, help="max number of quits/leaves between 2 points")
parser.add_argument("-d", "--days", type=int, default=28, help="number of days for the simulated data")
parser.add_argument("course")
args = parser.parse_args()
import sys
fake_counts(args.course,
            args.period,
            args.students,
            args.delta,
            args.days)

