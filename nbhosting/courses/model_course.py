# pylint: disable=c0111, w1203

from pathlib import Path
import subprocess
import json
from importlib.util import (
    spec_from_file_location, module_from_spec)

from nbhosting.main.settings import sitesettings, logger

from .sectioning import Sections, default_sectioning, DEFAULT_TRACK
from .model_mapping import StaticMapping

from typing import Dict

# this is what we expect to find in a course custom tracks.py
CourseTracks = Dict[str, Sections]


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

    def _static_dir(self):
        return NBHROOT / "static" / self.coursename
    static_dir = property(_static_dir)


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


    # check course-provided tracks and provide reasonable defaults
    # returns a Sections object for a given track
    def _check_tracks(self, tracks: CourseTracks):
        type_ok = True
        if not isinstance(tracks, dict):
            type_ok = False
        elif not all(isinstance(v, Sections) for v in tracks.values()):
            type_ok = False
        if not type_ok:
            logger.error("{self}: misformed tracks()")
        return type_ok


    # locate a Sections corresponding to trackaname in tracks
    def _locate_sections(self, tracks: CourseTracks, trackname) -> Sections:
        # is the track present ?
        if trackname in tracks:
            return tracks[trackname]
        # find some default
        logger.warning(
            f"tracks for {self.coursename} has no {trackname} track")
        if DEFAULT_TRACK in tracks:
            return tracks[DEFAULT_TRACK]
        # still not found, return the first one
        logger.warning(
            f"no {DEFAULT_TRACK} track, returning the first one")
        for value in tracks.values:
            return value

    # actually call tracks() if customized for course
    # return default strategy if missing or unable to run
    def _fetch_course_custom_tracks(self):
        """
        locate and load <course>/nbhosting/tracks.py

        objective is to make this customizable so that some
        notebooks in the repo can be ignored
        and the others organized along different view points

        the tracks() function will receive self as its single parameter
        it is expected to return a dictionary
           track_name -> Sections instance
        see flotpython/courses/nbhosting/tracks.py for a realistic example

        the keys in this dictionary are used in the web interface
        to propose the list of available tracks

        absence of tracks.py, or inability to run it, triggers
        the default policy (per directory) implemented in sectioning.py
        """
        course_root = (self.git_dir).absolute()
        course_tracks = course_root / "nbhosting/tracks.py"

        if course_tracks.exists():
            modulename = (f"{self.coursename}_tracks"
                          .replace("-", "_"))
            try:
                logger.debug(
                    f"{self} loading module {course_tracks}")
                spec = spec_from_file_location(
                    modulename,
                    course_tracks,
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
        else:
            logger.info(
                f"{self} no nbhosting hook found\n"
                f"expected in {course_tracks}")
        logger.warning(f"{self} resorting to default sectioning")
        return {DEFAULT_TRACK: default_sectioning(self)}


    def tracks(self):
        """
        returns the list of supported track names
        """
        return list(self._fetch_course_custom_tracks().keys())


    def sections(self, track=DEFAULT_TRACK):
        """
        returns a Sections object that describe the contents
        of that track

        implement caching in courses/<coursename>/.tracks/<track>.json
        this is important because opening all notebooks to
        retrieve their notebookname is quite slow

        cache needs to be cleaned up each time a course is updated from git
        and the nbh shell script does so
        """
        track = track if track is not None else DEFAULT_TRACK
        storage = self.notebooks_dir / ".tracks" / (track + ".json")
        storage.parent.mkdir(parents=True, exist_ok=True)
        try:
            with storage.open() as reader:
                dictionary = json.loads(reader.read())
                sections = Sections.loads(self, dictionary)
                logger.debug(f"{self}:{track} using cached sections")
                return sections
        except FileNotFoundError:
            pass
        except Exception as exc:
            logger.exception('{self}:{track} found but unloadable json')
        logger.info(f"{self}: re-reading sections for track {track}")
        tracks = self._fetch_course_custom_tracks()
        if not self._check_tracks(tracks):
            return default_sectioning(self)
        sections = self._locate_sections(tracks, track)
        try:
            with storage.open('w') as writer:
                dictionary = sections.dumps()
                writer.write(json.dumps(dictionary))
        except Exception as exc:
            logger.exception(f"{self}:{track} failed to save json")
        return sections


    def _probe_settings(self):
        notebooks_dir = self.notebooks_dir

        self.static_mappings = []
        path = (self.git_dir /
                "nbhosting" / "static-mappings")
        try:
            with path.open() as storage:
                for line in storage:
                    mapping = StaticMapping(line)
                    if mapping:
                        self.static_mappings.append(mapping)
        except FileNotFoundError:
            logger.info(f"mappings file not found {path}")
            self.static_mappings = StaticMapping.defaults()
        except Exception as exc:
            logger.exception(f"could not load static-mappings for {self}")
            self.static_mappings = StaticMapping.defaults()

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
