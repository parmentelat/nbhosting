import os.path
import time

from collections import OrderedDict

from nbhosting.settings import nbhosting_settings, logger

# xxx
# would be probably best to aggregate
# on a hourly basis instead of a daily basis
# xxx

# attach to one day
class DayFigures:
    def __init__(self):
        self.students = set()
        self.cumulative_students = set()
        self.notebooks = set()
        self.cumulative_notebooks = set()

class Stats:

    root = nbhosting_settings['root']

    time_format = "%Y-%m-%dT%H:%M:%SZ"
    day_format = "%Y-%m-%d"


    def __init__(self, course):
        self.course = course

    def events_filename(self):
        return os.path.join(self.root, "stats", self.course, "events.raw")
    def counts_filename(self):
        return os.path.join(self.root, "stats", self.course, "counts.raw")
    
    ####################
    def _write_events_line(self, student, notebook, action, port, timestamp=None):
        timestamp = timestamp or time.strftime(self.time_format, time.gmtime())
        filename = self.events_filename()
        course = self.course
        try:
            with open(filename, "a") as f:
                f.write("{timestamp} {course} {student} {action} {notebook} {port}\n".
                        format(**locals()))
        except:
            logger.error("Cannot store stats line into {}".format(filename))
    

    def record_open_notebook(self, student, notebook, action, port):
        """
        add one line in the events file for that course
        action is one of the three actions returned by run-student-course-jupyter
        port is the port number for that jupyter 
        """
        return self._write_events_line(student, notebook, action, port)

    def record_kill_jupyter(self, student):
        """
        add one line in the stats file for that course
        has 6 fields as well, althought the last 2 ones are just -
        """
        return self._write_events_line(student, '-', 'killing', '-')

    ####################
    def record_jupyters_count(self, running, frozen, timestamp=None):
        timestamp = timestamp or time.strftime(self.time_format, time.gmtime())
        filename = self.counts_filename()
        try:
            with open(filename, 'a') as f:
                f.write("{timestamp} {running} {frozen}\n"
                        .format(**locals()))
        except Exception as e:
            logger.error("Cannot store counts line into {} {}".format(filename, e))
        
    ####################
    def metrics_per_day(self):
        """
        read the events file for that course and produce
        a tuple of data arrays suitable for metricsgrahicsjs
        
        returns:
        # first is students per day
        [ { "date" : "2016-12-30", "value" : 20 }, ... ]
        # second is same but cumulative (not additive, based on set union)
        [ { "date" : "2016-12-30", "value" : 20 }, ... ]
        # third is the total number of notebooks opened that day
        """
        filename = self.events_filename()
        # a dictionary day -> figures
        day_figures = OrderedDict()
        try:
            with open(filename) as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        timestamp, course, student, action, notebook, port = line.split()
                        day = timestamp.split('T')[0]
                        day_figures.setdefault(day, DayFigures())
                        figures = day_figures[day]
                        figures.students.add(student)
                        if action not in ('killing'):
                            figures.notebooks.add(notebook)
                    except:
                        logger.error("{}:{}: skipped misformed line".format(filename, lineno))
                        continue
    
            # we have the day's students, let's cumulate
            days = list(day_figures.keys())
            # first cell needs to be dealt with separately
            if days:
                day1 = days[0]
                figures1 = day_figures[day1]
                figures1.cumulative_students = figures1.students
                figures1.cumulative_notebooks = figures1.notebooks
            # add yesterday's cumulative to today's studs to get today's cumulative
            for yesterday, today in zip(days, days[1:]):
                day_figures[today].cumulative_students \
                    = day_figures[yesterday].cumulative_students \
                    | day_figures[today].students
                day_figures[today].cumulative_notebooks \
                    = day_figures[yesterday].cumulative_notebooks \
                    | day_figures[today].notebooks
            
        except:
            pass
        finally:
            students_per_day = [
                { "date" : day,
                  "value" : len(figures.students)}
                for day, figures in day_figures.items()]
            cumulative_students_per_day = [
                { "date" : day,
                  "value" : len(figures.cumulative_students)}
                for day, figures in day_figures.items()]
            notebooks_per_day = [
                { "date" : day,
                  "value" : len(figures.notebooks)}
                for day, figures in day_figures.items()]
            cumulative_notebooks_per_day = [
                { "date" : day,
                  "value" : len(figures.cumulative_notebooks)}
                for day, figures in day_figures.items()]
            
            return \
                students_per_day, cumulative_students_per_day,\
                notebooks_per_day, cumulative_notebooks_per_day,


    def counts_points(self):
        """
        read the counts file for that course and produce
        data arrays suitable for metricsgrahicsjs

        returns
        # first is number of running jupyters; precision is the second
        [ { "date" : "2016-12-30 12:30:45", "value" : 20 }, ... ]
        # second : ditto with frozen containers
        [ { "date" : "2016-12-30 12:30:45", "value" : 20 }, ... ]
        """
        filename = self.counts_filename()
        runnings, totals = [], []
        try:
            with open(filename) as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        timestamp, running, frozen = line.split()
                        running, frozen = int(running), int(frozen)
                        jstime= timestamp.replace('T', ' ').replace('Z', '')
                        runnings.append({'date' : jstime, 'value' : running})
                        totals.append({'date' : jstime, 'value' : running+frozen})
                    except:
                        logger.error("{}:{}: skipped misformed line".format(filename, lineno))
        except:
            pass
        finally:
            return runnings, totals

if __name__ == '__main__':
    import sys
    course = 'flotbioinfo' if len(sys.argv) == 1 else sys.argv[1]
    mg = Stats(course).metrics_per_day()
    for m in mg:
        print(m)
