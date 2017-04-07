#!/usr/bin/env python3
import os
import random
import time

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

"""
This code produces random data for testing the stats view
of course it is not meant to run in production
"""

from nbhosting.stats.stats import Stats

actions = ['created', 'restarted', 'running', 'killing']

# def record_open_notebook(self, student, notebook, action, port):

def fake_events(course, nb_notebooks, nb_students, events, days, beg=None):

    stats = Stats(course)
    path = stats.notebook_events_path()
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
    
    nb_notebooks = int(nb_notebooks)
    nb_students = int(nb_students)
    events = int(events)

    if beg is None:
        beg = time.time()
    beg = int(beg)
    end = beg + days * 24 * 3600

    notebooks = [ "notebook-{:02d}".format(i+1) for i in range(nb_notebooks)]
    students = [ "student-{:05d}".format(i+1) for i in range(nb_students)]

    print("Generating (unsorted) fake events for course {}".format(course))
    print("with {} notebooks, {} students".format(nb_notebooks, nb_students))
    print("made of {} events over {} days".format(events, days))
    print("starting {}".format(
        time.strftime(Stats.time_format, time.localtime(beg))))

    for i in range(events):
        notebook = random.choice(notebooks)
        action = random.choice(actions)
        student = random.choice(students)
        epoch = random.randint(beg, end)
        timestamp = time.strftime(Stats.time_format, time.localtime(epoch))

        stats._write_events_line(student, notebook, action, 0, timestamp)

    command = "sort {f} > {f}.sorted; mv -f {f}.sorted {f}"\
              .format(f=path)
    print("Sorting with command {}".format(command))
    os.system(command)        

# pass course name as sys.argv[1] with optional args
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--notebooks", type=int, default=100, help="number of notebooks")
parser.add_argument("-s", "--students", type=int, default=4000, help="number of students")
parser.add_argument("-e", "--events", type=int, default=5000, help="total number of events")
parser.add_argument("-d", "--days", type=int, default=28, help="number of days for the simulated data")
parser.add_argument("course")
args = parser.parse_args()
fake_events(args.course,
            args.notebooks,
            args.students,
            args.events,
            args.days)
