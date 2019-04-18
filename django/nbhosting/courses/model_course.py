# pylint: disable=c0111, w1203

import os
from pathlib import Path                                # pylint: disable=w0611
import subprocess

from importlib.util import (
    spec_from_file_location, module_from_spec)

import docker

from nbh_main.settings import NBHROOT, logger

from .model_track import Track, generic_track
from .model_track import write_tracks, read_tracks
from .model_mapping import StaticMapping

# helper
def show_and_run(command, *, dry_run=False):
    if not dry_run:
        logger.info(f"# {command}")
        os.system(command)
    else:
        logger.info(f"(DRY-RUN) # {command}")


# this is what we expect to find in a course custom tracks.py
from typing import List
CourseTracks = List[Track]


class CourseDir:

    def __init__(self, coursename):
        self.coursename = coursename
        # historical default is no autopull
        self.autopull = False
        self._probe_settings()
        self._notebooks = None
        self._tracks = None


    def is_valid(self):
        return self.git_dir.exists() and self.git_dir.is_dir()
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

    def _static_dir(self):
        return NBHROOT / "static" / self.coursename
    static_dir = property(_static_dir)

    def _build_dir(self):
        return NBHROOT / "images" / self.coursename
    build_dir = property(_build_dir)


    def customized(self, filename):
        """
        given a filename, search this:
        * first in nbhroot/local/coursename/<filename>
        * second in nbhroot/courses-git/coursename/nbhosting/<filename>

        returns a Path instance, or None
        """
        c1 = NBHROOT / "local" / self.coursename / filename
        c2 = self.git_dir / "nbhosting" / filename

#        logger.debug(f"{self}.customized({filename})")
#        logger.debug(f"local={c1}")
#        logger.debug(f"in course repo={c2}")

        for c in (c1, c2):
            if c.exists():
#                logger.debug(f"using {c}")
                return c
        return None


    # for templating
    def length(self):
        """
        number of sections
        """
        return len(self)

    def notebooks(self):
        """
        sorted list of notebook paths
        """
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


    def student_dir(self, student):
        return NBHROOT / "students" / student / self.coursename

    def probe_student_notebooks(self, student):
        root = self.student_dir(student)
        return self._probe_notebooks_in_dir(root)



    def student_homes(self):
        """
        return the number of students who have that course in their home dir
        """
        student_course_dirs = (
            NBHROOT / "students").glob(f"*/{self.coursename}")
        # can't use len() on a generator
        return sum((1 for _ in student_course_dirs), 0)


    # check course-provided tracks and provide reasonable defaults
    # returns a Track object for a given track
    def _check_tracks(self, tracks: CourseTracks):
        type_ok = True
        if not isinstance(tracks, list):
            type_ok = False
        elif not all(isinstance(v, Track) for v in tracks):
            type_ok = False
        if not type_ok:
            logger.error("{self}: misformed tracks()")
        return type_ok


    # locate a Track corresponding to trackaname in tracks
    def _locate_track(self, tracks: CourseTracks, trackname) -> Track:
        for item in tracks:
            if item.name == trackname:
                return item
        # find some default
        if tracks:
            logger.warning(f"{self} has no {trackname} track - returning first track")
            return tracks[0]
        logger.warning("{self} has no track, returning generic")
        return generic_track(self)


    # actually call course-specific tracks()
    # return default strategy if missing or unable to run
    def _fetch_course_custom_tracks(self):
        """
        locate and load <course>/nbhosting/tracks.py

        objective is to make this customizable so that some
        notebooks in the repo can be ignored
        and the others organized along different view points

        the tracks() function will receive self as its single parameter
        it is expected to return a dictionary
           track_name -> Track instance
        see flotpython/courses/nbhosting/tracks.py for a realistic example

        the keys in this dictionary are used in the web interface
        to propose the list of available tracks

        absence of tracks.py, or inability to run it, triggers
        the default policy (per directory) implemented in model_track.py
        """

        course_tracks_py = self.customized("tracks.py")

        if course_tracks_py:
            modulename = (f"{self.coursename}_tracks"
                          .replace("-", "_"))
            try:
                logger.debug(
                    f"{self} loading module {course_tracks_py}")
                spec = spec_from_file_location(
                    modulename,
                    course_tracks_py,
                )
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                tracks_fun = module.tracks
                logger.debug(
                    f"triggerring {tracks_fun.__qualname__}()"
                )
                tracks = tracks_fun(self)
                if self._check_tracks(tracks):
                    return tracks
            except Exception:                           # pylint: disable=w0703
                logger.exception(
                    f"{self} could not do load custom tracks")
            finally:
                # make sure to reload the python code next time
                # we will need it, in case the course has published an update
                import sys
                if modulename in sys.modules:
                    del sys.modules[modulename]
        else:
            logger.info(
                f"{self} no tracks.py hook found")
        logger.warning(f"{self} resorting to generic filesystem-based track")
        return [generic_track(self)]


    def tracks(self):
        """
        returns a list of known tracks

        does this optimally, first use memory cache,
        disk cache in courses/<coursename>/.tracks.json
        and only then triggers course-specific tracks.py if provided
        """
        # in memory ?
        if self._tracks is not None:
            return self._tracks
        # in cache ?
        tracks_path = self.notebooks_dir / ".tracks.json"
        if tracks_path.exists():
            logger.debug(f"{tracks_path} found")
            tracks = read_tracks(self, tracks_path)
            self._tracks = tracks
            return tracks
        # compute from course
        logger.debug(f"{tracks_path} not found - recomputing")
        tracks = self._fetch_course_custom_tracks()
        self._tracks = tracks
        write_tracks(tracks, tracks_path)
        return tracks


    def tracknames(self):
        """
        returns the list of supported track names
        """
        return [track.name for track in self.tracks()]


    def track(self, trackname):
        """
        returns a Track object that maps that trackname
        """
        return self._locate_track(self.tracks(), trackname)


    def _probe_settings(self):
        notebooks_dir = self.notebooks_dir

        self.static_mappings = []
        custom_static_mappings = self.customized("static-mappings")
        if not custom_static_mappings:
            self.static_mappings = StaticMapping.defaults()
        else:
            try:
                with custom_static_mappings.open() as storage:
                    for line in storage:
                        mapping = StaticMapping(line)
                        if mapping:
                            self.static_mappings.append(mapping)
            except FileNotFoundError:
                # unfortunately this goes to stdout and
                # screws up the expose-static-* business
                #logger.info(f"mappings file not found {path}")
                self.static_mappings = StaticMapping.defaults()
            except Exception as exc:
                logger.exception(f"could not load static-mappings for {self}")
                self.static_mappings = StaticMapping.defaults()

        # store in raw format for nbh script
        with (self.notebooks_dir / ".static-mappings").open('w') as raw:
            for static_mapping in self.static_mappings:
                print(static_mapping.expose(self),
                      file=raw)
        toplevels = StaticMapping.static_toplevels(
            self.static_mappings
        )
        with (self.notebooks_dir / ".static-toplevels").open('w') as raw:
            for toplevel in toplevels:
                print(toplevel, file=raw)


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

        # autopull: file exists -> True
        try:
            with (notebooks_dir / ".autopull").open() as storage:
                self.autopull = True
        except Exception as exc:
            self.autopull = False


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


    def build_image(self, force=False):
        """
        locates Dockerfile and triggers docker build
        """
        force_tag = "" if not force else "--no-cache"
        build_dir = self.build_dir

        image = self.image
        if image != self.coursename:
            logger.warning(
                f"cowardly refusing to rebuild image {image}"
                f" from course {self.coursename}\n"
                f"the 2 names should match")
            return

        dockerfile = self.customized("Dockerfile")
        if not dockerfile or not dockerfile.exists():
            logger.error(
                f"Could not spot Dockerfile for course {self.coursename}")
            return

        # clean up and repopulate build dir
        show_and_run(f"rm -rf {build_dir}/*")
        build_dir.exists() or build_dir.mkdir()         # pylint: disable=w0106

        show_and_run(f"cp {dockerfile} {build_dir}/Dockerfile")
        show_and_run(f"cp {NBHROOT}/images/start-in-dir-as-uid.sh {build_dir}")
        show_and_run(f"cd {build_dir}; "
                     f"docker build {force_tag} -f Dockerfile -t {image} .")


    def pull_from_git(self):
        """
        pulls from the git repository
        """
        return self.run_nbh_subprocess('course-update-from-git')


    def destroy_student_container(self, student):
        container_name = f"{self.coursename}-x-{student}"
        client = docker.from_env()
        try:
            container = client.containers.get(container_name)
        except docker.errors.NotFound:
            logger.info(f"nothing to do - container {container_name} not found")
            return
        if container.status == 'running':
            logger.info(f"killing {container_name}")
            container.kill()
        logger.info(f"removing {container_name}")
        container.remove()
        logger.info("DONE")


    # useful when a shell-written feature is needed from python
    # we don't provide for calling nbh-manage, because in this case
    # it means the code is in python, so using imports is preferrable
    def run_nbh_subprocess(self, subcommand, *args, **run_args):
        """
        creates an instance of subprocess.CompletedProcess
        and prints stdout, stderr and returncode

        returns True when returncode is 0

        Parameters:
          args: additional arguments to subcommand
          run_args: additional arguments to subprocess.run();
            typically encoding="utf-8" is useful when text output is expected
            which in our case is always the case..
        """
        completed = self.nbh_subprocess(subcommand, False, *args, **run_args)

        print(f"{30*'='} {completed.args} → {completed.returncode}")
        print(f"{20*'='} stdout")
        print(f"{completed.stdout}")
        print(f"{20*'='} stderr")
        print(f"{completed.stderr}")

        return completed.returncode == 0



    def nbh_subprocess(self, subcommand, python, *args, **run_args):
        """
        return an instance of subprocess.CompletedProcess

        Parameters:
          python: the default is to call pain nbh; when python is set to True,
            the `nbh-manage` command is used instead
          args: additional arguments to subcommand
          run_args: additional arguments to subprocess.run();
            typically encoding="utf-8" is useful when text output is expected
            which in our case is always the case..
        """
        main = "nbh-manage" if python else "nbh"
        command = [main, subcommand, self.coursename] + list(args)
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8",
            **run_args)
