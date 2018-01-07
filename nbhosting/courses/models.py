from pathlib import Path
import subprocess

from nbhosting.main.settings import sitesettings

root = Path(sitesettings.root)


class CourseDir:

    def __init__(self, coursename):
        self.coursename = coursename
        self.notebooks_dir = root / "courses" / self.coursename
        self._probe_settings()
        self._notebooks = None

    def notebooks(self):
        if self._notebooks is None:
            self._notebooks = self._probe_notebooks()
        return self._notebooks

    def _probe_notebooks(self):
        notebooks_dir = self.notebooks_dir
        absolute_notebooks = notebooks_dir.glob("**/*.ipynb")
        # relative notebooks without extension
        return sorted([
            notebook.relative_to(notebooks_dir).with_suffix("")
            for notebook in absolute_notebooks
            if 'ipynb_checkpoints' not in str(notebook)
        ])

    def _probe_settings(self):
        notebooks_dir = self.notebooks_dir

        try:
            with (notebooks_dir / ".statics").open() as storage:
                self.statics = {line.strip() for line in storage if line}
        except Exception as e:
            self.statics = ["-- undefined -- {err}".format(err=e)]

        try:
            with (notebooks_dir / ".image").open() as storage:
                self.image = storage.read().strip()
        except Exception as e:
            self.image = "-- undefined -- {err}".format(err=e)

        try:
            with (notebooks_dir / ".staff").open() as storage:
                self.staff = {line.strip() for line in storage if line}
        except Exception as e:
            self.staff = []

        try:
            with (notebooks_dir / ".giturl").open() as storage:
                self.giturl = storage.read().strip()
        except Exception as e:
            self.giturl = "-- undefined -- {err}".format(err=e)

    def image_hash(self, docker_proxy):
        """
        the hash of the image that should be used for containers
        in this course
        or None if something goes wrong
        """
        try:
            return docker_proxy.images.get(self.image).id
        except:
            # xxx should log the exception
            import traceback
            traceback.print_exc()
            return

    def _run_nbh(self, subcommand, *args):
        """
        return an instance of subprocess.CompletedProcess
        """
        command = [ 'nbh', subcommand, self.coursename] + list(args)
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def update_from_git(self): return self._run_nbh("course-update-from-git")
    def build_image(self): return self._run_nbh("course-build-image")
    def clear_staff(self): return self._run_nbh("course-clear-staff")

    def student_homes(self):
        """
        return the number of students who have that course in their home dir
        """
        student_course_dirs = (
            root / "students").glob("*/{}".format(self.coursename))
        # can't use len() on a generator
        return sum((1 for _ in student_course_dirs), 0)


class CoursesDir:

    def __init__(self):
        subdirs = (root / "courses-git").glob("*")
        self._coursenames = sorted([subdir.name for subdir in subdirs])

    def coursenames(self):
        return self._coursenames
