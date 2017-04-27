from pathlib import Path
import time

from collections import OrderedDict

from nbhosting.main.settings import nbhosting_settings, logger

root = Path(nbhosting_settings['root'])

# attach to a given day
class DailyFigures:
    """
    keep track of the activity during a given day, as compared
    to the previous day
    in order to avoid useless expensive set copies, when moving to the next day, 
    caller must call the wrap() method that does accounting
    """
    def __init__(self, previous=None):
        self.students = set()
        self.notebooks = set()
        if previous is None:
            self.cumul_students = set()
            self.cumul_notebooks = set()
        else:
            self.cumul_students = previous.cumul_students
            self.cumul_notebooks = previous.cumul_notebooks

    def add_student(self, student):
        self.students.add(student)

    def add_notebook(self, notebook):
        self.notebooks.add(notebook)

    def wrap(self):
        self.nb_unique_students = len(self.students)
        self.nb_unique_notebooks = len(self.notebooks)
        self.nb_new_students = len(self.students - self.cumul_students)
        self.nb_new_notebooks = len(self.notebooks - self.cumul_notebooks)
        self.cumul_students.update(self.students)
        self.cumul_notebooks.update(self.notebooks)


class Stats:

    # using localtime in all raw files
    time_format = "%Y-%m-%dT%H:%M:%S"


    def __init__(self, course):
        self.course = course
        self.course_dir = root / "raw" / self.course
        self.course_dir.mkdir(parents=True, exist_ok=True)

    ####################
    def notebook_events_path(self):
        return self.course_dir / "events.raw"
    def monitor_counts_path(self):
        return self.course_dir / "counts.raw"
    
    ####################
    def _write_events_line(self, student, notebook, action, port, timestamp=None):
        timestamp = timestamp or time.strftime(self.time_format, time.localtime())
        path = self.notebook_events_path()
        course = self.course
        try:
            with path.open("a") as f:
                f.write("{timestamp} {course} {student} {notebook} {action} {port}\n".
                        format(**locals()))
        except:
            logger.error("Cannot store stats line into {}".format(path))
            import traceback
            traceback.print_exc()

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
    def record_monitor_counts(self, running_containers, frozen_containers,
                              running_kernels, students_count,
                              timestamp=None):
        timestamp = timestamp or time.strftime(self.time_format, time.localtime())
        path = self.monitor_counts_path()
        try:
            with path.open('a') as f:
                f.write("{} {} {} {} {}\n"
                        .format(timestamp, running_containers, frozen_containers,
                                running_kernels, students_count))
        except Exception as e:
            logger.error("Cannot store counts line into {} {}".format(path, e))
        
    ####################
    def daily_metrics(self):
        """
        read the events file for that course and produce
        data arrays suitable for being composed under plotly
        
        returns a dict with the following components
        * 'daily': { 'timestamps', 'new_students', 'new_notebooks',
                     'unique_students', 'unique_notebooks' }
          - all 5 same size
          (one per day, time is always 23:59:59)
        * 'events': { 'timestamps', 'total_students', 'total_notebooks' } 
           - all 3 same size
        """
        events_path = self.notebook_events_path()
        # a dictionary day -> figures
        figures_by_day = OrderedDict()
        previous_figures = None
        current_figures = DailyFigures()
        # results
        events_timestamps = []
        total_students = []
        total_notebooks = []
        try:
            with events_path.open() as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        timestamp, course, student, notebook, action, port = line.split()
                        day = timestamp.split('T')[0] + ' 23:59:59'
                        if day in figures_by_day:
                            current_figures = figures_by_day[day]
                        else:
                            current_figures.wrap()
                            previous_figures = current_figures
                            current_figures = DailyFigures(previous_figures)
                            figures_by_day[day] = current_figures
                        # if action is 'killing' it means we already know
                        # about that notebook, right ? so let's count this notebook
                        # no matter what, it makes the code less brittle
                        current_figures.add_notebook(notebook)
                        current_figures.add_student(student)
                        events_timestamps.append(timestamp)
                        total_students.append(len(current_figures.cumul_students))
                        total_notebooks.append(len(current_figures.cumul_notebooks))
                    except Exception as e:
                        logger.error("{}:{}: skipped misformed events line - {}: {}"
                                     .format(events_path, lineno, type(e), e))
                        continue
        except Exception as e:
            logger.exception("unexpected exception")
        finally:
            current_figures.wrap()
            daily_timestamps = []
            unique_students = []
            unique_notebooks = []
            new_students = []
            new_notebooks = []

            for timestamp, figures in figures_by_day.items():
                daily_timestamps.append(timestamp)
                unique_students.append(figures.nb_unique_students)
                unique_notebooks.append(figures.nb_unique_notebooks)
                new_students.append(figures.nb_new_students)
                new_notebooks.append(figures.nb_new_notebooks)

            return { 'daily' : { 'timestamps' : daily_timestamps,
                                 'unique_students' : unique_students,
                                 'unique_notebooks' : unique_notebooks,
                                 'new_students' : new_students,
                                 'new_notebooks' : new_notebooks},
                     'events' : { 'timestamps' : events_timestamps,
                                  'total_students' : total_students,
                                  'total_notebooks' : total_notebooks}}
                
    def monitor_counts(self):
        """
        read the counts file for that course and produce
        data arrays suitable for plotly

        returns a dictionary with the following keys
        'timestamps' : the times where monitor reported the figures
        'running_jupyters': running containers
        'total_jupyters' :  total containers
        'running_kernels' : sum of open notebooks 
        'student_homes' : number of students that have this course in their homedir 
        """
        counts_path = self.monitor_counts_path()
        timestamps = []
        running_jupyters = []
        total_jupyters = []
        running_kernels = []
        student_counts = []
        try:
            with counts_path.open() as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        timestamp, *values = line.split()
                        # xxx could be more flexible if we ever add counters in there
                        rj, fj, rk, sc = [int(value) for value in values]
                        jstime= timestamp.replace('T', ' ')
                        timestamps.append(jstime)
                        running_jupyters.append(rj)
                        total_jupyters.append(rj + fj)
                        running_kernels.append(rk)
                        student_counts.append(sc)
                        logger.info("adding one monitor counts")
                    except Exception as e:
                        logger.error("{}:{}: skipped misformed counts line - {}: {}"
                                     .format(counts_path, lineno, type(e), e))
        except:
            pass
        finally:
            return {
                'timestamps' : timestamps,
                'running_jupyters' : running_jupyters,
                'total_jupyters' : total_jupyters,
                'running_kernels' : running_kernels,
                'student_counts' : student_counts
            }

if __name__ == '__main__':
    import sys
    course = 'flotbioinfo' if len(sys.argv) == 1 else sys.argv[1]
    mg = Stats(course).daily_metrics()
    for k, v in mg.items():
        print(k, v)
