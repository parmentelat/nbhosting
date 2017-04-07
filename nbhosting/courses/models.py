from pathlib import Path
import subprocess

from nbhosting.main.settings import nbhosting_settings

root = Path(nbhosting_settings['root'])

class CourseDir:

    def __init__(self, coursename):
        self.coursename = coursename
        self._notebooks = None

    def notebooks(self):
        if self._notebooks is None:
            self._notebooks = self._probe_notebooks()
        return self._notebooks

    def _probe_notebooks(self):
        course_root = root / "courses" / self.coursename
        absolute_notebooks = course_root.glob("**/*.ipynb")
        # relative notebooks without extension
        return [
            notebook.relative_to(course_root).with_suffix("")
            for notebook in absolute_notebooks
            if 'ipynb_checkpoints' not in str(notebook)
        ]
    
    def update_completed(self):
        """
        return an instance of subprocess.CompletedProcess
        """
        command = [ "nbh-update-course", root, self.coursename]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return completed

    def students_count(self):
        """
        return the number of students who have that course in their home dir
        """
        student_course_dirs = (root / "students").glob("*/{}".format(self.coursename))
        # can't use len() on a generator
        return sum((1 for _ in student_course_dirs), 0)

class CoursesDir:

    def __init__(self):
        subdirs = (root / "courses-git").glob("*")
        self._coursenames = [ subdir.name for subdir in subdirs ]

    def coursenames(self):
        return self._coursenames
        
