import os.path
import time

from nbhosting.settings import nbhosting_settings

root = nbhosting_settings['root']

time_format = "%Y-%m-%dT%H:%M:%SZ"

def stats_filename(course):
    return os.path.join(root, "stats", course, "stats.raw")

def stat_open_notebook(course, student, notebook, action, port):
    timestamp = time.strftime(time_format, time.gmtime())
    filename = stats_filename(course)
    try:
        with open(filename, "a") as f:
            f.write("{timestamp} {course} {student} {notebook} {action} {port}\n".
                    format(**locals()))
    except:
        print("ERROR ! - Cannot store stats line into {}".format(filename))

