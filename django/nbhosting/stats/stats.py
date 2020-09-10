from pathlib import Path
import time
import re
import itertools
from datetime import timedelta
from collections import OrderedDict, defaultdict

from nbhosting.stats.timebuckets import TimeBuckets
from nbhosting.courses.model_course import CourseDir
from nbh_main.settings import sitesettings, logger

nbhroot = Path(sitesettings.nbhroot)

# using gmtime in all raw files
time_format = "%Y-%m-%dT%H:%M:%S"

# this is to skip artefact-users like e.g. 'student'
# used to have regexps for edx-like hashes,
# but proved too restrictive for users from m@gistere
# who were asked to forge their hashes in separate namespaces
# so for now let's just keep the long ones
def artefact_user(user_hash):
    # actual students get a username in first.last
    # so this should be considered real
    if '.' in user_hash:
        return False
    return len(user_hash) < 28

# an iterable has no builtin len method
def iter_len(iterable):
    count = 0
    for _ in iterable:
        count += 1
    return count


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
        self._nb_total_students = len(self.cumul_students)
        self._nb_total_notebooks = len(self.cumul_notebooks)


    def add_student(self, student):
        if student not in self.students and student not in self.cumul_students:
            self._nb_total_students += 1
        self.students.add(student)
    def add_notebook(self, notebook):
        if notebook not in self.notebooks and notebook not in self.cumul_notebooks:
            self._nb_total_notebooks += 1
        self.notebooks.add(notebook)


    # we call these zillions of times, can't afford to
    # compute a set union each time we need this
    def nb_total_students(self):
        # return len(self.students | self.cumul_students)
        return self._nb_total_students
    def nb_total_notebooks(self):
        # return len(self.notebooks | self.cumul_notebooks)
        return self._nb_total_notebooks


    def wrap(self):
        self.nb_unique_students = len(self.students)
        self.nb_unique_notebooks = len(self.notebooks)
        self.nb_new_students = len(self.students - self.cumul_students)
        self.nb_new_notebooks = len(self.notebooks - self.cumul_notebooks)
        self.cumul_students.update(self.students)
        self.cumul_notebooks.update(self.notebooks)


class TotalsAccumulator:
    """
    if we do not pay attention we end up issuing way too many events
    so they need to be filtered out a bit

    an accumulator essentially remembers stuff like

    timestamps = [14:00 14:05 14:08 15:00] some time stamps (in fact a longer format is used)
    students =   [12    13    14    15]    number of students known at that time
    notebooks =  [20    20    21    22]    number of notebooks opened at least once at that time

    """
    def __init__(self):
        self.timestamps = []
        # these 2 will remember numbers of students or of notebooks
        self.students = []
        self.notebooks = []
        self.last_t, self.last_s, self.last_n = None, None, None


    def _insert(self, timestamp, nb_students, nb_notebooks):
        self.timestamps.append(timestamp)
        self.students.append(nb_students)
        self.notebooks.append(nb_notebooks)


    def insert(self, timestamp, nb_students, nb_notebooks):
        # in all cases, remember the last one, so we are sure to mention it at the end
        self.last_t, self.last_s, self.last_n = timestamp, nb_students, nb_notebooks
        # object is empty, record without thinking more
        if not self.timestamps:
            self._insert(timestamp, nb_students, nb_notebooks)
            return
        # same numbers as the previous entry : skip
        if nb_students == self.students[-1] and nb_notebooks == self.notebooks[-1]:
            return
        # otherwise : insert it
        self._insert(timestamp, nb_students, nb_notebooks)


    def wrap(self):
        # nothing to remember
        if self.last_t is None:
            return
        # check if we have recorded this event
        if self.timestamps[-1] == self.last_t \
           and self.students[-1] == self.last_s \
           and self.notebooks[-1] == self.last_n:
            pass
        # record it
        self._insert(self.last_t, self.last_s, self.last_n)


class Stats:


    def __init__(self, coursename):
        self.coursename = coursename
        self.course_dir = nbhroot / "raw" / self.coursename
        self.course_dir.mkdir(parents=True, exist_ok=True)

    ####################
    def notebook_events_path(self):
        return self.course_dir / "events.raw"
    def monitor_counts_path(self):
        return self.course_dir / "counts.raw"

    ####################
    def _write_events_line(self, student, notebook, action, port):
        timestamp = time.strftime(time_format, time.gmtime())
        path = self.notebook_events_path()
        coursename = self.coursename
        try:
            with path.open("a") as f:
                f.write(f"{timestamp} {coursename} {student} {notebook} {action} {port}\n")
        except Exception as exc:
            logger.exception(f"Cannot store stats line into {path}, {type (exc)}")

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
    # every cycle the monitor writes a counts line
    # with a predefined set of integer counts
    # and we want this to be extensible over time
    # this is the list - in that order - of arguments
    # to record_monitor_counts
    known_counts = [
        'running_container', 'frozen_container',
        'running_kernel',
        'student_home',
        'load1', 'load5', 'load15',
        'container_ds_percent', 'container_ds_free',
        'nbhosting_ds_percent', 'nbhosting_ds_free',
        'system_ds_percent', 'system_ds_free',
        'memory_total', 'memory_free', 'memory_available',
        'system_container', 'system_kernel',
    ]

    def record_monitor_known_counts_line(self):
        # timestamp = time.strftime(time_format, time.gmtime())
        path = self.monitor_counts_path()
        try:
            with path.open('a') as f:
                f.write("# " + " ".join(self.known_counts) + "\n")
        except Exception as exc:
            logger.exception(f"Cannot store headers line into {path}, {type(exc)}")

    def record_monitor_counts(self, *args):
        timestamp = time.strftime(time_format, time.gmtime())
        path = self.monitor_counts_path()
        if len(args) > len(self.known_counts):
            logger.error(f"two many arguments to counts line "
                         f"- dropped {args} from {path}")
        try:
            with path.open('a') as f:
                payload = " ".join(str(arg) for arg in args)
                f.write(f"{timestamp} {payload}\n")
        except Exception as exc:
            logger.exception(f"Cannot store counts line into {path}, {type(exc)}")

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
        # the events dimension
        accumulator = TotalsAccumulator()
        #
        staff_names = {username for username in CourseDir.objects.get(coursename=self.coursename).staff_usernames.split()}
        try:
            with events_path.open() as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        timestamp, _coursename, student, notebook, action, _port = line.split()
                        # if action is 'killing' then notebook is '-'
                        # which should not be counted as a notebook of course
                        # so let's ignore these lines altogether
                        if action == 'killing':
                            continue
                        # ignore staff or other artefact users
                        if student in staff_names or artefact_user(student):
                            continue
                        day = timestamp.split('T')[0] + ' 23:59:59'
                        if day in figures_by_day:
                            current_figures = figures_by_day[day]
                        else:
                            current_figures.wrap()
                            previous_figures = current_figures
                            current_figures = DailyFigures(previous_figures)
                            figures_by_day[day] = current_figures
                        current_figures.add_notebook(notebook)
                        current_figures.add_student(student)
                        accumulator.insert(
                            timestamp,
                            current_figures.nb_total_students(),
                            current_figures.nb_total_notebooks())
                    except Exception as exc:
                        logger.exception(f"{events_path}:{lineno}: "
                                         f"skipped misformed events line {type(exc)}:{line}")
                        continue
        except Exception as _exc:
            logger.exception("unexpected exception in daily_metrics")
        finally:
            current_figures.wrap()
            accumulator.wrap()
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
                     'events' : { 'timestamps' : accumulator.timestamps,
                                  'total_students' : accumulator.students,
                                  'total_notebooks' : accumulator.notebooks}}

    def monitor_counts(self):
        """
        read the counts file for that course and produce
        data arrays suitable for plotly

        returns a dictionary with the following keys
        * 'timestamps' : the times where monitor reported the figures
        * plus, for each known count as listed in known_counts,
          a key made plural by adding a 's', so e.g.
         'running_jupyters': running containers
        """
        counts_path = self.monitor_counts_path()
        timestamps = []
        counts = { count: [] for count in self.known_counts}
        known_counts = self.known_counts
        max_counts = len(known_counts)
        try:
            with counts_path.open() as f:
                for lineno, line in enumerate(f, 1):
                    if line.startswith('#'):
                        # ignore any comment
                        continue
                    try:
                        timestamp, *values = line.split()
                        timestamps.append(timestamp)
                        # each line should have at most len(known_counts)
                        # and should all contain integers
                        if len(values) > max_counts:
                            logger.error(f"{counts_path}:{lineno}: "
                                         f"counts line has too many fields " 
                                         f"- {len(values)} > {max_counts}")
                            continue
                        ivalues = [int(v) for v in values]
                        for count, ivalue in zip(known_counts, ivalues):
                            counts[count].append(ivalue)
                        # fill in for missing values
                        missing = max_counts - len(values)
                        if missing > 0:
                            for count in known_counts[-missing:]:
                                counts[count].append(None)
                    except Exception as _exc:
                        logger.exception(f"{counts_path}:{lineno}: "
                                         f"skipped misformed counts line - {line}")
        except:
            pass
        finally:
            # add as many keys (with an extra 's') as we have known keys
            result = { f"{count}s" : counts[count] for count in self.known_counts }
            # do not forget the timestamps
            result['timestamps'] = timestamps
            return result

    def material_usage(self):
        """
        read the events file and produce data about relations
        between notebooks and students
        remember we cannot serialize a set, plus a sorted result is better
        'nbstudents' : how many students are considered (test students are removed..)
        'nbstudents_per_notebook' : a sorted list of tuples (notebook, nb_students)
                                  how many students have read this notebook
        'nbstudents_per_notebook_animated' : same but animated over time
        'nbstudents_per_nbnotebooks' : a sorted list of tuples (nb_notebooks, nb_students)
                                  how many students have read exactly that number of notebooks
        'heatmap' : a complete matrix notebook x student ready to feed to plotly.heatmap
                    comes with 'x', 'y' and 'z' keys
        """

        events_path = self.notebook_events_path()
        # a dict notebook -> set of students
        set_by_notebook = defaultdict(set)
        nbstudents_per_notebook_buckets = TimeBuckets(grain=timedelta(hours=6),
                                                      time_format=time_format)
        # a dict student -> set of notebooks
        set_by_student = defaultdict(set)
        # a dict hashed on a tuple (notebook, student) -> number of visits
        raw_counts = defaultdict(int)
        #
        staff_names = {username for username in
                       CourseDir.objects.get(coursename=self.coursename).staff_usernames.split()}
        try:
            with events_path.open() as f:
                for _lineno, line in enumerate(f, 1):
                    date, _, student, notebook, action, *_ = line.split()
                    # action 'killing' needs to be ignored
                    if action in ('killing',):
                        continue
                    # ignore staff or other artefact users
                    if student in staff_names or artefact_user(student):
                        logger.debug(f"ignoring staff or artefact student {student}")
                        continue
                    # animated data must be taken care of before anything else
                    previous, next, changed = nbstudents_per_notebook_buckets.prepare(date)
                    if changed:
                        nspn = [ (notebook, len(set_by_notebook[notebook]))
                                for notebook in sorted(set_by_notebook)]
                        nbstudents_per_notebook_buckets.record_data(nspn, previous, next)
                    set_by_notebook[notebook].add(student)
                    set_by_student[student].add(notebook)
                    raw_counts[notebook, student] += 1
        except Exception as _exc:
            logger.exception(f"could not read {events_path} to count students per notebook")

        finally:
            nbstudents_per_notebook = [
                (notebook, len(set_by_notebook[notebook]))
                for notebook in sorted(set_by_notebook)
            ]
            nb_by_student = { student: len(s) for (student, s) in set_by_student.items() }

            nbstudents_per_notebook_animated = nbstudents_per_notebook_buckets.wrap(nbstudents_per_notebook)

            # counting in the other direction is surprisingly tedious
            nbstudents_per_nbnotebooks = [
                (number, iter_len(v))
                for (number, v) in itertools.groupby(sorted(nb_by_student.values()))
            ]
            # the heatmap
            heatmap_notebooks = sorted(set_by_notebook.keys())
            heatmap_students = sorted(set_by_student.keys())
            # a first attempt at showing the number of times a given notebook was open
            # by a given student resulted in poor outcome
            # problem being mostly with colorscale, we'd need to have '0' stick out
            # as transparent or something, but OTOH sending None instead or 0
            heatmap_z = [
                [raw_counts.get( (notebook, student,), None) for notebook in heatmap_notebooks]
                for student in heatmap_students
            ]
            # sort students on total number of opened notebooks
            heatmap_z.sort(key = lambda student_line: sum(x for x in student_line if x))

            zmax = max((max(x for x in line if x) for line in heatmap_z),
                       default=0)
            zmin = min((min(x for x in line if x) for line in heatmap_z),
                       default=0)

            return {
                'nbnotebooks' : len(set_by_notebook),
                'nbstudents' : len(set_by_student),
                'nbstudents_per_notebook' : nbstudents_per_notebook,
                'nbstudents_per_notebook_animated' : nbstudents_per_notebook_animated,
                'nbstudents_per_nbnotebooks' : nbstudents_per_nbnotebooks,
                'heatmap' : {'x' : heatmap_notebooks, 'y' : heatmap_students,
                             'z' : heatmap_z,
                             'zmin' : zmin, 'zmax' : zmax,
                },
            }
