# pylint: disable=c0111

from pathlib import Path
import subprocess

from nbhosting.main.settings import sitesettings, logger

NBHROOT = Path(sitesettings.nbhroot)


class CourseDir:

    def __init__(self, coursename):
        self.coursename = coursename
        self.notebooks_dir = NBHROOT / "courses" / self.coursename
        self._probe_settings()
        self._notebooks = None

    def notebooks(self):
        if self._notebooks is None:
            self._notebooks = self._probe_sorted_notebooks()
        return self._notebooks

    @staticmethod
    def _probe_notebooks_in_dir(root):
        absolute_notebooks = root.glob("**/*.ipynb")
        # relative notebooks without extension
        return (
            notebook.relative_to(root).with_suffix("")
            for notebook in absolute_notebooks
            if 'ipynb_checkpoints' not in str(notebook)
        )

    def _probe_sorted_notebooks(self):
        return sorted(
            self._probe_notebooks_in_dir(self.notebooks_dir)
        )

    def probe_student_notebooks(self, student):
        root = NBHROOT / "students" / student / self.coursename
        return self._probe_notebooks_in_dir(root)

    def _probe_settings(self):
        notebooks_dir = self.notebooks_dir

        try:
            with (notebooks_dir / ".statics").open() as storage:
                self.statics = {
                    line.strip() for line in storage if line}
        except Exception as exc:
            self.statics = {f"-- undefined -- {exc}"}

        try:
            with (notebooks_dir / ".image").open() as storage:
                self.image = storage.read().strip()
        except Exception as exc:
            self.image = f"-- undefined -- {exc}"

        try:
            with (notebooks_dir / ".staff").open() as storage:
                self.staff = {
                    line.strip() for line in storage if line}
        except Exception:
            self.staff = set()

        try:
            with (notebooks_dir / ".giturl").open() as storage:
                self.giturl = storage.read().strip()
        except Exception as exc:
            self.giturl = f"-- undefined -- {exc}"

    def image_hash(self, docker_proxy):
        """
        the hash of the image that should be used for containers
        in this course
        or None if something goes wrong
        """
        try:
            return docker_proxy.images.get(self.image).id
        except:
            logger.exception("Can't figure image hash")
            return

    def _run_nbh(self, subcommand, *args, **run_args):
        """
        return an instance of subprocess.CompletedProcess

        Parameters:
          args: additional arguments to subcommand
          run_args: additional arguments to subprocess.run(); typically
            *encoding="utf-8"* is useful when text output is expected

        """
        command = ['nbh', subcommand, self.coursename] + list(args)
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **run_args)

    def update_from_git(self):
        return self._run_nbh("course-update-from-git", encoding="utf-8")
    def build_image(self):
        return self._run_nbh("course-build-image", encoding="utf-8")
    def clear_staff(self):
        return self._run_nbh("course-clear-staff", encoding="utf-8")

    def student_homes(self):
        """
        return the number of students who have that course in their home dir
        """
        student_course_dirs = (
            NBHROOT / "students").glob("*/{}".format(self.coursename))
        # can't use len() on a generator
        return sum((1 for _ in student_course_dirs), 0)

    def student_home(self, student):
        """
        Returns a list of dicts like
          notebook, in_course, in_student
        """
