# pylint: disable=c0111

from pathlib import Path
import subprocess
import json
from importlib.util import (
    spec_from_file_location, module_from_spec)

from nbhosting.main.settings import sitesettings, logger

from .sectioning import Sections, Section, default_sectioning


NBHROOT = Path(sitesettings.nbhroot)


class CourseDir:

    def __init__(self, coursename):
        self.coursename = coursename
        self._probe_settings()
        self._notebooks = None

    def __repr__(self):
        return self.coursename

    def __len__(self):
        return len(self.notebooks())

    def _notebooks_dir(self):
        return NBHROOT / "courses" / self.coursename
    notebooks_dir = property(_notebooks_dir)

    def _git_dir(self):
        return NBHROOT / "courses-git" / self.coursename
    git_dir = property(_git_dir)


    # for templating
    def length(self):
        return len(self)

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



    def student_homes(self):
        """
        return the number of students who have that course in their home dir
        """
        student_course_dirs = (
            NBHROOT / "students").glob(f"*/{self.coursename}")
        # can't use len() on a generator
        return sum((1 for _ in student_course_dirs), 0)



    def sections(self, viewpoint="course"):
        """
        Search in cache first because opening all notebooks to
        retrieve their notebookname is quite slow

        cache should be cleaned up each time a course is updated from git
        """
        storage = self.notebooks_dir / ".viewpoints" / (viewpoint + ".json")
        storage.parent.mkdir(parents=True, exist_ok=True)
        try:
            with storage.open() as reader:
                dictionary = json.loads(reader.read())
                sections = Sections.loads(self, dictionary)
                logger.debug(f"{self} using cached sections for {viewpoint}")
                return sections
        except FileNotFoundError:
            pass
        except Exception as exc:
            logger.exception('')
        logger.info(f"{self}: re-reading sections for viewpoint {viewpoint}")
        sections = self._sections(viewpoint)
        with storage.open('w') as writer:
            dictionary = sections.dumps()
            writer.write(json.dumps(dictionary))
        return sections


    def _sections(self, viewpoint="course"):
        """
        return a list of relevant notebooks
        arranged in sections

        there's a default sectioning code that will group
        notebooks per subdir

        objective is to make this customizable so that some
        notebooks in the repo can be ignored
        and the others organized along different view points

        this can be done through a python module named
        nbhosting/sectioning.py
        that should expose a function named
        sections(coursedir, viewpoint)
        viewpoint being for now 'course' but could be used
        to define other subsets (e.g. exercises, videos, ...)
        that function is expected to return a list of
        * either Section objects
        * or of dicts like
         { 'name': str,
           'notebooks': <a list of notebook paths>}
        """
        course_root = (self.git_dir).absolute()
        course_viewpoints = course_root / "nbhosting/viewpoints.py"

        if course_viewpoints.exists():
            modulename = (f"{self.coursename}_viewpoints"
                          .replace("-", "_"))
            try:
                logger.debug(
                    f"loading module {course_viewpoints}")
                spec = spec_from_file_location(
                    modulename,
                    course_viewpoints,
                )
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                sections_fun = module.sections
                logger.debug(
                    f"triggerring {sections_fun.__qualname__}"
                )
                return sections_fun(self, viewpoint)
            except Exception as exc:
                logger.exception(f"could not do custom sectioning"
                                 f" course={self.coursename}"
                                 f" viewpoint={viewpoint}")
        else:
            logger.info(f"no nbhosting hook found for course {self}\n"
                        f"expected in {course_viewpoints}")
        return default_sectioning(self)


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
