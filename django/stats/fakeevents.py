#!/usr/bin/env python3
import os
import random
import time

"""
This code produces random data for testing the stats view
of course it is not meant to run in production
"""

from stats import Stats

actions = ['created', 'restarted', 'running', 'killing']

# def record_open_notebook(self, student, notebook, action, port):

def fake_events(course, nb_notebooks=100, nb_students=4000, hits=5000, days=28, beg=None):

    stats = Stats(course)
    filename = stats.events_filename()
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
    
    nb_notebooks = int(nb_notebooks)
    nb_students = int(nb_students)
    hits = int(hits)

    if beg is None:
        beg = time.time()
    beg = int(beg)
    end = beg + days * 24 * 3600

    notebooks = [ "notebook-{:02d}".format(i+1) for i in range(nb_notebooks)]
    students = [ "student-{:05d}".format(i+1) for i in range(nb_students)]

    print("Generating (unsorted) fake events for course {}".format(course))
    print("with {} notebooks, {} students".format(nb_notebooks, nb_students))
    print("made of {} hits over {} days".format(hits, days))
    print("starting {}".format(
        time.strftime(Stats.time_format, time.gmtime(beg))))

    for i in range(hits):
        notebook = random.choice(notebooks)
        action = random.choice(actions)
        student = random.choice(students)
        epoch = random.randint(beg, end)
        timestamp = time.strftime(Stats.time_format, time.gmtime(epoch))

        stats._write_events_line(student, notebook, action, 0, timestamp)

    command = "sort {f} > {f}.sorted; mv -f {f}.sorted {f}"\
              .format(f=filename)
    print("Sorting with command {}".format(command))
    os.system(command)        

# pass course name as sys.argv[1] with optional args
import sys
args = sys.argv[1:]
fake_events(*args)

