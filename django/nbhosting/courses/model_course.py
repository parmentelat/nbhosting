# pylint: disable=c0111
# pylint: disable=logging-fstring-interpolation, f-string-without-interpolation
# pylint: disable=attribute-defined-outside-init
# pylint: disable=broad-except
# pylint: disable=expression-not-assigned
# pylint: disable=imported-auth-user
# pylint: disable=no-else-return

import os
import itertools
import re
from pathlib import Path                                          # pylint: disable=w0611
import yaml
import copy
import subprocess
import shutil

from importlib.util import (spec_from_file_location, module_from_spec)

import podman

from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template

from nbh_main.settings import NBHROOT, logger, sitesettings

from nbhosting.utils import show_and_run

from .model_track import (
    Track, generic_track, tracks_from_yaml_config,
    CourseTracks, write_tracks, read_tracks, sanitize_tracks)
from .model_mapping import StaticMapping
from .model_build import Build

from ..matching import matching_policy

CLASSIC_NOTEBOOK_URL_FORMAT = "notebooks/{notebook}"
# used as a default for non-notebooks - see edxfront/views.py
JLAB_NOTEBOOK_URL_FORMAT = "lab/tree/{notebook}"

# default is to use classic notebook
DEFAULT_NOTEBOOK_URL_FORMAT = CLASSIC_NOTEBOOK_URL_FORMAT

PODMAN_URL = "unix:///run/podman/podman.sock"

class CourseDir(models.Model):                  # pylint: disable=too-many-public-methods

    coursename = models.CharField(max_length=128)
    giturl = models.CharField(max_length=1024, default='none')
    image = models.CharField(max_length=256, default='none')
    autopull = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    autobuild = models.BooleanField(default=False)

    # staff users refer to hashes created remotely
    # so they do not match locally registered users
    # so it is *not* a many-to-many relationship
    # xxx this should be private, use the staffs property below
    # but kept this name to avoid a db migration
    staff_usernames = models.TextField(default="", blank=True)

    # this OTOH qualifies for a proper n-to-n thing
    registered_groups = models.ManyToManyField(
        Group, related_name='courses_registered'
    )

    def __init__(self, *args, **kwds):
        self._notebooks = None
        # reconfigurable
        # could become a property
        self._tracks = None
        self.notebook_url_format = DEFAULT_NOTEBOOK_URL_FORMAT
        self.builds = []
        self.static_mappings = []
        super().__init__(*args, **kwds)

    def __str__(self): # pylint: disable=invalid-str-returned
        return self.coursename


    def __lt__(self, other):
        return self.coursename < other.coursename

    @property
    def staffs(self):
        # use @group syntax to mention all the members of a group
        result = set()
        for token in self.staff_usernames.split():            # pylint: disable=no-member
            if not token.startswith('@'):
                result.add(token)
            else:
                groupname = token[1:]
                try:
                    result.update(
                        user.username
                        for user in Group.objects.get(name=groupname).user_set.all())
                except ObjectDoesNotExist:
                    logger.error(f"ignoring unknown group {groupname}"
                                 f" in staffs for {self.coursename}")
        return result


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
        return str(self.coursename)
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

    def drop_dir(self):
        return NBHROOT / "droparea" / self.coursename


    def dropareas(self):
        for droppath in self.drop_dir().glob('*'):
            if droppath.is_dir():
                yield droppath.name

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
        for dir_ in all_dirs:
            dir_kind = dir_.parent.name
            if dir_kind == 'raw':
                if clean_raw:
                    clear(dir_)
            else:
                clear(dir_)
        if not preserve_students:
            student_spaces = (NBHROOT / "students" / self.coursename).glob("*")
            for dir_ in student_spaces:
                clear(dir_)

    def customized_s(self, filename):
        """
        implements the standard way to search for custom files
        either locally, or by the course itself

        given a filename, return all the files if they exist in:
        * first in nbhroot/local/coursename/<filename>
        * second in nbhroot/courses-git/coursename/nbhosting/<filename>
        * or third in nbhroot/courses-git/coursename/.nbhosting/<filename>

        also a warning is issued if both files are found in nbhosting and .nbhosting

        returns a list of Path instances
        """
        candidates = [
            NBHROOT / "local" / self.coursename / filename,
            self.git_dir / "nbhosting" / filename,
            self.git_dir / ".nbhosting" / filename,
        ]
        existing = [x for x in candidates if x.exists()]

        if candidates[1] in existing and candidates[2] in existing:
            logger.warn(f"in {self}, found {filename} in both nbhosting and .nbhosting")

        return existing


    def customized(self, filename):
        """
        implements the first found customized

        returns a Path instance, or None
        """
        candidates = self.customized_s(filename)
        return candidates[0] if candidates else None


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
        container_name = f"{self.coursename}-x-{student}"
        try:
            with podman.PodmanClient(base_url=PODMAN_URL) as podman_api:
                podman_api.containers.get(container_name).kill()
                return True
        except podman.errors.NotFoundError:
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

        staff_set = set(self.staff_usernames.split())
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
                              quiet_mode=False, do_pull=False,
                              reset_if_needed=False, always_reset=False):
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
        if always_reset:
            command = ( f"nbh-pull-student"
                        f" -R"
                        f" {'-q' if quiet_mode else ''}"
                        f" {self.coursename} {user.username} {user_workspace} "
                        f" {course_hash} {user_hash}")
            os.system(command)
        else:
            if self.does_current_hash_have(course_hash, user.username, user_hash):
                myqprint(f"OK> student {user.username}")
                return
            # if we set only reset, this means to pull
            if not (do_pull or reset_if_needed):
                print(f"!! {self.coursename}/{user.username} is behind on {user_hash}")
                return
            # here we are in a position to try an reconcile the student's repo
            # with upstream
            # for now we go for an external shell script that is easier
            # to develop in incremental deployment mode
            command = (f"nbh-pull-student"
                    f" {'-r' if reset_if_needed else ''}"
                    f" {'-q' if quiet_mode else ''}"
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


    def i_registered_users(self):
        """
        returns an iterator over the set of User instances
        that are part of any of the registered groups
        """
        users = set()
        for group in self.registered_groups.all():
            for user in group.user_set.all():
                if user in users:
                    continue
                users.add(user)
                yield user

    def nb_registered_users(self):
        """
        the total number of registered users
        """
        return sum(1 for _ in self.i_registered_users())

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
    @staticmethod
    def _check_tracks(tracks: CourseTracks):
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
        cache_path = self.notebooks_dir / ".tracks.json"
        if cache_path.exists():
            logger.debug(f"tracks saved from cache {cache_path}")
            tracks = read_tracks(self, cache_path)
            self._tracks = tracks
            return tracks
        # compute from yaml config
        if self._yaml_config and 'tracks' in self._yaml_config:
            tracks_filter = self._yaml_config.get('tracks-filter', [])
            logger.debug(f"computing tracks from yaml using {tracks_filter=}")
            tracks = tracks_from_yaml_config(
                self, self._yaml_config['tracks'], tracks_filter)
        else:
            logger.debug(f"using generic track")
            tracks = [generic_track(self)]
        tracks = sanitize_tracks(tracks)
        self._tracks = tracks
        write_tracks(tracks, cache_path)
        return tracks


    def tracknames(self):
        """
        returns the list of supported track names
        """
        return [track.name for track in self.tracks()]

    def default_trackname(self):
        try:
            return self.tracks()[0].name
        except Exception:
            return "unknown"


    def track(self, trackname):
        """
        returns a Track object that maps that trackname
        """
        return self._locate_track(self.tracks(), trackname)


    def _probe_settings(self):
        self._yaml_config = None
#        self._probe_settings_yaml() or self._probe_settings_old()
        self._probe_settings_yaml()
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

    DEFAULT_SETTINGS = {
        'general': {
            'notebook-url-format': DEFAULT_NOTEBOOK_URL_FORMAT,
        },
        'tracks': [],
        'tracks-filter': [],
        'static-mappings': [],
        'builds': [],
        'builds-filter': [],
    }

    # by default, merging means update dictionaries and extend lists
    # however, there are exceptions
    DEFAULT_SETTINGS_POLICY = {
        # if the local course provides a tracks-filter field,
        # it will overwrite/supersede - not extend - any
        # setting done in the course itself
        'tracks-filter': 'overwrite',
        # same for builds-filter
        'builds-filter': 'overwrite',
    }

    def _probe_settings_yaml(self):

        yaml_filenames = self.customized_s("nbhosting.yaml")
        logger.debug(f"{yaml_filenames=}")
        if not yaml_filenames:
            return False

        yaml_configs = []
        for yaml_filename in yaml_filenames:
            try:
                with open(yaml_filename) as feed:
                    yaml_configs.append(yaml.safe_load(feed.read()))
            except Exception:
                logger.exception(f"could not load yaml file {yaml_filename} - ignoring")

        # initialize and merge all
        yaml_config = self.merge_settings(yaml_configs)

        if 'general' in yaml_config and 'notebook-url-format' in yaml_config['general']:
            self.notebook_url_format = yaml_config['general']['notebook-url-format']

        self.static_mappings = (
            StaticMapping.defaults()
            if not yaml_config.get('static-mappings', None)
            else [StaticMapping(D['source'], D['destination'])
                for D in yaml_config['static-mappings']
            ])

        self.builds = [Build(D, self) for D in yaml_config.get('builds', [])]
        # if one needs to remove all builds, it won't work to set builds-filter to []
        # because this is considered as the default value for builds-filter
        # just define builds-filter with a list that contains a non-existing build id
        if 'builds-filter' in yaml_config:
            filter = yaml_config['builds-filter']
            if filter:
                self.builds = [build for build in self.builds
                            if build.id in filter]

        self._yaml_config = yaml_config
        return True


    def merge_settings(self, yamls: list):
        """
        return a clean merge of all the yaml files found
        """
        if not yamls:
            logger.error(f"cannot merge empty settings")
            return {}

        # since customized_s returns highest-precedence first
        # we need to reverse that list
        yamls = yamls[::-1]
        result = copy.deepcopy(self.DEFAULT_SETTINGS)
        for key, default in self.DEFAULT_SETTINGS.items():
            policy = self.DEFAULT_SETTINGS_POLICY.get(key, 'merge')
            for index, layer in enumerate(yamls, 1):
                if policy == 'overwrite':
                    if key in layer:
                        result[key] = layer[key]
                elif policy == 'merge':
                    if isinstance(default, list):
                        result[key].extend(layer.get(key, []))
                    elif isinstance(default, dict):
                        result[key].update(layer.get(key, {}))

        return result


    def image_hash(self):
        """
        the hash of the image that should be used for containers
        in this course
        or None if something goes wrong
        """
        with podman.PodmanClient(base_url=PODMAN_URL) as podman_api:
            try:
                return podman_api.images.get(self.image).attrs['Id']
            except podman.errors.ImageNotFound:
                logger.error(f"Course {self.coursename} "
                            f"uses unknown podman image {self.image}")
            except Exception:
                logger.exception("Can't figure image hash")
        return None


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

    def run_image_details(self):
        """
        spawns a container and execute a command to get details
        on the various versions inside the container
        rough - outputs in the terminal
        """
        commands = []
        commands.append("python --version")
        commands.append("jupyter --version")
        commands.append("pip freeze | grep ==")
        bundle = ';'.join(commands)
        overall = f"podman run --rm {self.image} bash -cx '{bundle}'"
        print(overall)
        os.system(overall)


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

    def run_build(self, build: Build, *,  # pylint: disable=too-many-locals
                  dry_run=False, force=False):
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

        if not build.script:
            logger.warning(f"build {build.name} has no script - skipping")
            return False

        coursename = self.coursename
        githash = self.current_hash()

        buildid = build.id
        script = build.script                           # pylint: disable=unused-variable
        directory = build.directory                     # pylint: disable=unused-variable
        result_folder = build.result_folder             # pylint: disable=unused-variable
        entry_point = build.entry_point                 # pylint: disable=unused-variable

        build_path = Path(self.build_dir) / buildid / githash
        if build_path.exists():
            if not build_path.is_dir():
                logger.error(f"{build_path} exists and is not a dir - build aborted")
                return False
            if not force:
                logger.warning(f"build {build_path} already present - run with --force to override")
                return False
            logger.info(f"removing existing build (--force) {build_path}")
            shutil.rmtree(str(build_path))

        variables = "NBHROOT+coursename+script+directory+result_folder"
        # oddly enough a dict comprehension won't work here,
        # saying the variable names are undefined...
        vars_ = {}
        for var in variables.split('+'):
            vars_[var] = eval(var)                             # pylint: disable=eval-used

        template = get_template("scripts/dot-clone-build-rsync.sh")
        expanded_script = template.render(vars_)

        host_trigger = build_path / ".clone-build-rsync.sh"
        host_log = host_trigger.with_suffix(".log")
        host_trigger.parent.mkdir(parents=True, exist_ok=True)
        with host_trigger.open('w') as writer:
            writer.write(expanded_script)

        container = f"{coursename}-xbuildx-{buildid}-{githash}"

        podman_c  = f""
        podman_c += f" podman run --rm"
        podman_c += f" --name {container}"
        # mount git repo
        podman_c += f" -v {self.git_dir}:{self.git_dir}"
        # ditto under its normalized name if needed
        if self.norm_git_dir != self.git_dir:
            podman_c += f" -v {self.norm_git_dir}:{self.norm_git_dir}"
        # mount subdir of NBHROOT/builds
        podman_c += f" -v {host_trigger.parent}:/home/jovyan/building"
        podman_c += f" {self.image}"
        podman_c += f" bash /home/jovyan/building/.clone-build-rsync.sh"
        podman_c += f" > {host_log} 2>&1"
        success = show_and_run(podman_c, dry_run=dry_run)
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
        return success

    def pull_from_git(self, silent=False):
        """
        pulls from the git repository
        """
        if self.archived:
            print("WARNING: not pulling an archived course")
            return False
        if not silent:
            result = self.run_nbh_subprocess('course-update-from-git')
        else:
            completed = self.nbh_subprocess('course-update-from-git', False)
            result = (completed.returncode == 0)
        return result


    def current_branch(self):
        """
        returns branch name of the source repo in courses-dir
        """
        directory = self.git_dir
        command=['git', '-C', str(directory), 'rev-parse', '--abbrev-ref', 'HEAD']
        return subprocess.run(
            command, capture_output=True, check=False).stdout.decode().strip()


    def current_hash(self, student=None):
        """
        returns full hash of current commit, either in the student's
        directory, or in the main course git area if not provided
        """
        directory = self.git_dir if not student else self.student_dir(student)
        command=['git', '-C', str(directory), 'log', '-1', "--pretty=%h"]
        return subprocess.run(
            command, capture_output=True, check=False).stdout.decode().strip()


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
            encoding="utf-8", check=False,
            **run_args)


    def has_build_buttons(self):
        """
        returns True if the course has at least one build
        with at least one build button
        """
        self.probe()
        return any(build.has_buttons_to_expose() for build in self.builds)
