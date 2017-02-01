#!/usr/bin/env python3
import random
import time

"""
This code produces random data for testing the stats view
of course it is not meant to run in production
"""

from stats import Stats

def fake_counts(course, period=10, nb_students=4000, delta=50 , days=28, beg=None):

    """
    period is in minutes
    delta is the max difference between 2 points
    """

    stats = Stats(course)
    filename = stats.counts_filename()
    # make sure the file is void
    can_open = False
    try:
        with open(filename) as f:
            can_open = f.read()
    except:
        pass

    if can_open:
        print("wow wow wow: file={}".format(filename))
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
        time.strftime(Stats.time_format, time.gmtime(beg))))

    pointer = beg
    count = random.randint(0, nb_students + 1)
    
    while pointer <= end:
        count = random.randint(max(0, count - delta),
                               min(count + delta, nb_students + 1))
        timestamp = time.strftime(Stats.time_format, time.gmtime(pointer))
        stats._write_counts_line('jupyters', count, timestamp)
        pointer += period*60


# pass course name as sys.argv[1] with optional args
import sys
args = sys.argv[1:]
fake_counts(*args)

