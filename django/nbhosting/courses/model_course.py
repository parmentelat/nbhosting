# pylint: disable=c0111

import os
from pathlib import Path                                # pylint: disable=w0611
import subprocess
import shutil
import itertools
import re
import yaml

from importlib.util import (
    spec_from_file_location, module_from_spec)

import podman
podman_url = "unix://localhost/run/podman/podman.sock"

from django.db import models
from django.contrib.auth.models import User, Group
from django.template.loader import get_template

from nbh_main.settings import NBHROOT, logger, sitesettings

from nbhosting.utils import show_and_run

from .model_track import (
    Track, generic_track, tracks_from_yaml_config,
    CourseTracks, write_tracks, read_tracks, sanitize_tracks)
from .model_mapping import StaticMapping
from .model_build import Build

from ..matching import matching_policy


class CourseDir(models.Model):

    coursename = models.CharField(max_length=128)
    giturl = models.CharField(max_length=1024, default='none')
    image = models.CharField(max_length=256, default='none')
    autopull = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    # staff users refer to hashes created remotely
    # so they do not match locally registered users
    # so it is *not* a many-to-many relationship
    staff_usernames = models.TextField(default="", blank=True)

    # this OTOH qualifies for a proper n-to-n thing
    registered_groups = models.ManyToManyField(
        Group, related_name='courses_registered'
    )

    def __init__(self, *args, **kwds):
        self._notebooks = None
        self._tracks = None
        super().__init__(*args, **kwds)

    def __lt__(self, other):
        return self.coursename < other.coursename

    @staticmethod
    def courses_by_patterns(patterns):
        """
        a generator to iterate over the CourseDir objects
        whose name matches any of the given patterns
        * no pattern means all courses match
        * empty (string) pattern, or pattern = '*'
          means all courses
        * without any *
          all courses that contain that string match
        * otherwise: considered a full-feature regexp
        """
        def pattern_to_regexp(pattern):
            # implement above rule
            if not pattern or pattern == '*':
                return '^.*$'
            elif '*' not in pattern:
                return f'^.*{pattern}.*$'
            else:
                return pattern
        # no pattern means all
        patterns = patterns or ['']
        regexps = [re.compile(pattern_to_regexp(p)) for p in patterns]
        for coursedir in CourseDir.objects.all():
            name = coursedir.coursename
            if any(regexp.match(name) for regexp in regexps):
                yield coursedir


    # hopefully temporary; being a Model seems to imply
    # the constructor is not run when reloading at startup-time
    # so we need to call this explicitly when needed
    def probe(self):
        if hasattr(self, '_probed'):
            return
        try:
            self._probe_settings()
        finally:
            self._probed = True


    def is_valid(self):
        return self.git_dir.exists() and self.git_dir.is_dir()
    def __repr__(self):
        return self.coursename
    def archived_class(self):
        return "archived" if self.archived else ""

    def __len__(self):
        return len(self.notebooks())


    def _notebooks_dir(self):
        return NBHROOT / "courses" / self.coursename
    notebooks_dir = property(_notebooks_dir)

    def _git_dir(self):
        return NBHROOT / "courses-git" / self.coursename
    git_dir = property(_git_dir)
    # because NBHROOT and hence self.git_dir might be a symlink
    # typically a student repo would have its remote set to
    # remote.origin.url=/nbhosting/dev/courses-git/ue12-intro
    # but only /nbhosting/current would be visible from the container
    def _norm_git_dir(self):
        return self.git_dir.resolve()
    norm_git_dir = property(_norm_git_dir)

    def _static_dir(self):
        return NBHROOT / "static" / self.coursename
    static_dir = property(_static_dir)

    def _image_dir(self):
        return NBHROOT / "images" / self.coursename
    image_dir = property(_image_dir)

    def _build_dir(self):
        return NBHROOT / "builds" / self.coursename
    build_dir = property(_build_dir)


    def relevant(self, user):
        """
        is this group relevant for a given user

        if the user is is no group, then this returns True
        otherwise, it looks for an intersection between
        the groups from the course and the groups from the user
        """
        groups = user.groups.all()
        if not groups:
            return True
        both = groups & self.registered_groups.all()
        return bool(both)


    def clean_before_delete(self, *, preserve_students, clean_raw, verbose=True):
        all_dirs = NBHROOT.glob(f"*/{self.coursename}")
        def clear(path):
            if verbose:
                logger.info(f"Clearing {path}")
                shutil.rmtree(path)
        for dir in all_dirs:
            dir_kind = dir.parent.name
            if dir_kind == 'raw':
                if clean_raw:
                    clear(dir)
            else:
                clear(dir)
        if not preserve_students:
            student_spaces = (NBHROOT / "students" / self.coursename).glob("*")
            for dir in student_spaces:
                clear(dir)

    def customized(self, filename):
        """
        implements the standard way to search for custom files
        either locally, or by the course itself

        given a filename, search this:
        * first in nbhroot/local/coursename/<filename>
        * second in nbhroot/courses-git/coursename/nbhosting/<filename>

        returns a Path instance, or None
        """
        c1 = NBHROOT / "local" / self.coursename / filename
        c2 = self.git_dir / "nbhosting" / filename

        for c in (c1, c2):
            if c.exists():
                return c
        return None


    def notebooks(self):
        """
        sorted list of notebook paths
        """
        if self._notebooks is None:
            self._notebooks = self._probe_sorted_notebooks()
        return self._notebooks

    @staticmethod
    def _probe_notebooks_in_dir(root):
        absolute_notebooks = itertools.chain(
            *(root.glob(f"**/*.{extension}")
              for extension in sitesettings.notebook_extensions))
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


    def kill_student_container(self, student):
        """
        kills container attached to (course x student)

        returns True if container was killed, False otherwise
        """
        import podman
        podman_url = "unix://localhost/run/podman/podman.sock"
        container_name = f"{self.coursename}-x-{student}"
        try:
            with podman.ApiConnection(podman_url) as podman_api:
                return podman.containers.kill(podman_api, container_name)
        except podman.errors.ContainerNotFound:
            return False


    def users_with_workspace(self, *, user_patterns=None, staff_selector=None):
        """
        an iterator on tuples of the form
        (User, workspace_path)
        for all (registered) users who have a
        workspace open on that course
        and whose name matches the pattern, if provided

        user_patterns: see matching policy in module nbhosting.matching

        staff_selector:
          if not provided, defaults to {'student', 'staff'}
        """

        if isinstance(user_patterns, str):
            user_patterns = [user_patterns]

        if staff_selector is None:
            staff_selector = {'staff', 'selector'}

        staff_set = {user for user in self.staff_usernames.split()}
        def staff_match(user, staff_selector):
            if user.username in staff_set:
                return 'staff' in staff_selector
            else:
                return 'student' in staff_selector

        all_users = sorted(
            User.objects.all(),
            key=lambda user: user.username)
        for user in all_users:
            if not matching_policy(user.username, user_patterns):
                continue
            if not staff_match(user, staff_selector):
                continue
            user_workspace = self.student_dir(user.username)
            if not user_workspace.exists():
                continue
            yield user, user_workspace


    def update_user_workspace(self, user:User, *,
                              course_hash=None, user_workspace=None,
                              quiet_mode=False, do_pull=False):
        """
        allows to inspect or update a user's workspace

        if do_pull is False, the method only checks the user's current commit's hash
        with the course's hash

        if do_pull is True, this method will for now invoke the nbh-pull-student
        that for convenience is currently shipped as a standalone shell script
        mostly nbh-pull-student this will do a git pull, but try to smoothly
        accomodate our use cases where e.g. often differences are only
        with python version..

        quiet_mode asks for a less verbose output

        if either course_hash or user_workspace are already known,
        pass them along for more efficiency
        """
        if course_hash is None:
            course_hash = self.current_hash()
        if user_workspace is None:
            user_workspace = self.student_dir(user.username)
        user_hash = self.current_hash(user.username)

        def myqprint(*args):
            if not quiet_mode:
                print(*args)

        if not user_hash:
            myqprint(f"?? student {user.username} has a non-git workspace")
            return
        if course_hash == user_hash:
            myqprint(f"OK student {user.username}")
            return
        if self.does_current_hash_have(course_hash, user.username, user_hash):
            myqprint(f"OK> student {user.username}")
            return
        if not do_pull:
            print(f"!! {self.coursename}/{user.username} is behind on {user_hash}")
            return
        # here we are in a position to try an reconcile the student's repo
        # with upstream
        # for now we go for an external shell script that is easier
        # to develop in incremental deployment mode
        command = (f"nbh-pull-student {'-q' if quiet_mode else ''}"
                   f" {self.coursename} {user.username} {user_workspace} "
                   f" {course_hash} {user_hash}")
        os.system(command)
        # check again
        new_hash = self.current_hash(user.username)
        if new_hash == course_hash:
            myqprint(f"OK {user.username} pulled to {course_hash}")
        elif self.does_current_hash_have(course_hash, user.username, new_hash):
            myqprint(f"OK> {user.username} pulled to {course_hash}")
        else:
            print(f"!! {user.username} still behind on {new_hash}")


    def nb_student_homes(self):
        """
        the number of students who have that course in their home dir
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


    # locate a Track corresponding to trackname in tracks
    def _locate_track(self, tracks: CourseTracks, trackname) -> Track:
        for item in tracks:
            if item.id == trackname:
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
        see flotpython/nbhosting/tracks.py for a realistic example

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
        self.probe()
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
        # compute from yaml config
        if self._yaml_config and 'tracks' in self._yaml_config:
            logger.debug(f"computing tracks from yaml")
            tracks = tracks_from_yaml_config(self, self._yaml_config['tracks'])
        else:
            # compute from course
            logger.debug(f"{tracks_path} not found - recomputing")
            tracks = self._fetch_course_custom_tracks()
        tracks = sanitize_tracks(tracks)
        self._tracks = tracks
        write_tracks(tracks, tracks_path)
        return tracks


    def tracknames(self):
        """
        returns the list of supported track names
        """
        return [track.name for track in self.tracks()]

    def default_trackname(self):
        try:
            return self.tracks()[0].name
        except:
            return "unknown"


    def track(self, trackname):
        """
        returns a Track object that maps that trackname
        """
        return self._locate_track(self.tracks(), trackname)


    def _probe_settings(self):
        self._yaml_config = None
        self.static_mappings = []
        self.builds = []
        self._probe_settings_yaml() or self._probe_settings_old()
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


    def _probe_settings_yaml(self):
        yaml_filename = self.customized("nbhosting.yaml")
        logger.debug(f"yaml filename {yaml_filename}")
        if not yaml_filename:
            return False
        try:
            with open(yaml_filename) as feed:
                yaml_config = yaml.safe_load(feed.read())
            #
            if 'static-mappings' not in yaml_config:
                self.static_mappings = StaticMapping.defaults()
            else:
                logger.debug(f"populating static-mappings from yaml")
                self.static_mappings = [
                    StaticMapping(D['source'], D['destination'])
                    for D in yaml_config['static-mappings']
                ]
            #
            if 'builds' not in yaml_config:
                self.builds = []
            else:
                self.builds = [ Build(D) for D in yaml_config['builds'] ]
            self._yaml_config = yaml_config
        except Exception:
            logger.exception(f"could not load yaml file {yaml_filename} - ignoring")
            return False
        return True


    def _probe_settings_old(self):

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
            except Exception:
                logger.exception(f"could not load static-mappings for {self}")
                self.static_mappings = StaticMapping.defaults()



    def image_hash(self):
        """
        the hash of the image that should be used for containers
        in this course
        or None if something goes wrong
        """
        with podman.ApiConnection(podman_url) as podman_api:
            try:
                return podman.images.inspect(podman_api, self.image)['Id']
            except podman.errors.ImageNotFound:
                logger.error(f"Course {self.coursename} "
                            f"uses unknown podman image {self.image}")
            except:
                logger.exception("Can't figure image hash")


    def build_image(self, force=False, dry_run=False):
        """
        locates Dockerfile and triggers podman build
        """
        force_tag = "" if not force else "--no-cache"
        image_dir = self.image_dir

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
        show_and_run(f"rm -rf {image_dir}/*", dry_run=dry_run)
        image_dir.exists() or image_dir.mkdir()         # pylint: disable=w0106

        show_and_run(f"cp {dockerfile} {image_dir}/Dockerfile", dry_run=dry_run)
        show_and_run(f"cp {NBHROOT}/images/start-in-dir-as-uid.sh {image_dir}",
                     dry_run=dry_run)
        show_and_run(f"cd {image_dir}; "
                     f"podman build {force_tag} -f Dockerfile -t {image} .",
                     dry_run=dry_run)


    def list_builds(self, build_patterns):
        self.probe()
        for build in self.builds:
            if not matching_policy(build.name, build_patterns):
                continue
            print(build)

    def run_builds(self, build_patterns, *, dry_run=False, force=False):
        self.probe()
        for build in self.builds:
            if not matching_policy(build.name, build_patterns):
                continue
            self.run_build(build, dry_run=dry_run, force=force)

    def run_build(self, build: Build, *, dry_run=False, force=False):
        """
        execute one of the builds provided in nbhosting.yaml

        * preparation: create a launcher script called .clone-build-rsync.sh
          in NBHROOT/builds/<coursename>/<buildid>/<githash>/
          this script contains the 'script' part defined in YAML
          surrounded with some pre- and post- code
        * start a podman container with the relevant areas bind-mounted
          namely the git repo - mounted read-only - and the build area
          mentioned above

        return True if build is done or redone successfully
        """

        coursename = self.coursename
        githash = self.current_hash()

        buildid = build.id
        script = build.script
        directory = build.directory
        result_folder = build.result_folder
        entry_point = build.entry_point

        build_path = Path(self.build_dir) / buildid / githash
        if build_path.exists():
            if not build_path.is_dir():
                logger.error(f"{build_path} exists and is not a dir - build aborted")
                return False
            if not force:
                logger.error(f"build {build_path} already present - run with --force to override")
                return False
            logger.info(f"removing existing build (--force) {build_path}")
            import shutil
            shutil.rmtree(str(build_path))

        variables = "NBHROOT+coursename+script+directory+result_folder"
        # oddly enough a dict comprehension won't work here,
        # saying the variable names are undefined...
        vars = {}
        for var in variables.split('+'):
            vars[var] = eval(var)

        template = get_template("scripts/dot-clone-build-rsync.sh")
        expanded_script = template.render(vars)

        host_trigger = build_path / ".clone-build-rsync.sh"
        host_log = host_trigger.with_suffix(".log")
        host_trigger.parent.mkdir(parents=True, exist_ok=True)
        with host_trigger.open('w') as writer:
            writer.write(expanded_script)

        container = f"{coursename}-xbuildx-{buildid}-{githash}"

        podman  = f""
        podman += f" podman run --rm"
        podman += f" --name {container}"
        # mount git repo
        podman += f" -v {self.git_dir}:{self.git_dir}"
        # ditto under its normalized name if needed
        if self.norm_git_dir != self.git_dir:
            podman += f" -v {self.norm_git_dir}:{self.norm_git_dir}"
        # mount subdir of NBHROOT/builds
        podman += f" -v {host_trigger.parent}:/home/jovyan/building"
        podman += f" {self.image}"
        podman += f" bash /home/jovyan/building/.clone-build-rsync.sh"
        podman += f" > {host_log} 2>&1"
        success = show_and_run(podman, dry_run=dry_run)
        if dry_run:
            logger.info(f"(DRY-RUN) Build script is in {host_trigger}")
        else:
            logger.info(f"See complete log in {host_log}")
            if success:
                # move latest symlink
                latest = Path(self.build_dir) / buildid / "latest"
                latest.exists() and latest.unlink()
                latest.symlink_to(Path(githash), target_is_directory=True)
                logger.info(f"{latest} updated ")

    def pull_from_git(self, silent=False):
        """
        pulls from the git repository
        """
        if not silent:
            return self.run_nbh_subprocess('course-update-from-git')
        else:
            completed = self.nbh_subprocess('course-update-from-git', False)
            return completed.returncode == 0


    def current_hash(self, student=None):
        """
        returns full hash of current commit, either in the student's
        directory, or in the main course git area if not provided
        """
        directory = self.git_dir if not student else self.student_dir(student)
        command=['git', '-C', str(directory), 'log', '-1', "--pretty=%h"]
        return subprocess.run(
            command, capture_output=True).stdout.decode().strip()


    def does_current_hash_have(self, course_hash, student, student_hash):
        """
        useful for checking that a student's repo is in sync with the course

        the course is on hash 'course_hash'
        we need to check if the student is on a hash that
        already has the course_hash integrated

        this is done by using
        git merge-base --is-ancestor course student
        that should return 0
        """
        directory = self.student_dir(student)
        # check that the course hash is present on the student side
        command1 = ['git', '-C', str(directory),
                    'cat-file', '-e', course_hash, '2>/dev/null']
        command2 = ['git', '-C', str(directory),
                    'merge-base', '--is-ancestor', course_hash, student_hash]
        command = " ".join(command1) + ' && ' + " ".join(command2)
        return os.system(command) == 0


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

        Returns:
          True if the subprocess returns 0, False otherwise
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
        if not python:
            command = ["nbh", "-d", str(NBHROOT)]
        else:
            command = [ "nbh-manage" ]
        command += [subcommand, self.coursename] + list(args)
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8",
            **run_args)
