# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbhosting.matching import matching_policy

from nbh_main.settings import logger, NBHROOT

def iter_len(iter):
    return sum(1 for _ in iter)


def list_courses_groups(patterns, verbose):
    """
    usual verbosity meaning - see e.g. group_list.py
    """
    for coursedir in CourseDir.objects.all():
        if not matching_policy(coursedir.coursename, patterns):
            continue
        if verbose == 0:
            print(coursedir.coursename)
            continue
        groups = coursedir.registered_groups.all()
        if verbose == 1:
            print(f"{coursedir.coursename} has {iter_len(groups)} group(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {coursedir.coursename} has {iter_len(groups)} group(s)")
        for group in groups:
            print(group.name)


def list_courses_users(patterns, verbose):
    """
    usual verbosity meaning - see e.g. group_list.py
    """
    for coursedir in CourseDir.objects.all():
        if not matching_policy(coursedir.coursename, patterns):
            continue
        if verbose == 0:
            print(coursedir.coursename)
            continue
        users = sorted({user for user in coursedir.i_registered_users()},
                       key=lambda user: user.username)
        if verbose == 1:
            print(f"{coursedir.coursename} has {iter_len(users)} user(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {coursedir.coursename} has {iter_len(users)} user(s)")
        for user in users:
            print(user.username)

def list_courses_builds(patterns, verbose):
    for coursedir in CourseDir.objects.all():
        if not matching_policy(coursedir.coursename, patterns):
            continue
        coursedir.probe()
        for build in coursedir.builds:
            print(f"{coursedir.coursename} {build}")


def list_courses_staffs(patterns, verbose):
    """
    usual verbosity meaning - see e.g. group_list.py
    """
    for coursedir in CourseDir.objects.all():
        if not matching_policy(coursedir.coursename, patterns):
            continue
        if verbose == 0:
            print(coursedir.coursename)
            continue
        # a staff is just a plain str
        staffs = sorted(coursedir.staffs)
        if verbose == 1:
            print(f"{coursedir.coursename} has {iter_len(staffs)} staff(s)")
            continue
        if verbose >= 3:
            print(f"{10*'-'} {coursedir.coursename} has {iter_len(staffs)} staff(s)")
        for staff in staffs:
            print(staff)
        if verbose >=3:
            print(f"--- actual source (using groups) is\n{coursedir.staff_usernames}")


class Command(BaseCommand):

    help = """
    this command list known courses;

    without argument it lists all courses; with arguments
    it lists all course whose name contains any of the tokens;

    example: nbh-manage course-list python bio

    could output: bioinfo mines-python-primer
    python-slides python-mooc
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--list", action="count", default=0,
            dest='verbose',
            help=("Give more output. "
                  "Option is additive, and can be used up to 3 times."),
        )
        parser.add_argument(
            "-g", "--groups", default=False, action="store_true",
            help="only list registered groups",
        )
        parser.add_argument(
            "-u", "--users", default=False, action="store_true",
            help="only list users affiliated through at least one group",
        )
        parser.add_argument(
            "-b", "--builds", default=False, action="store_true",
            help="list builds",
        )
        parser.add_argument(
            "-s", "--staffs", default=False, action="store_true",
            help="list staff users"
        )
        parser.add_argument(
            "-i", "--image", default=False, action="store_true",
            dest='podman',
            help="if set, any missing !image! is notified as a warning "
            " - requires a working podman engine"
        )
        parser.add_argument("patterns", nargs='*', type=str)

    @staticmethod
    def dropareas(coursedir):
        dropareas = list(coursedir.dropareas())
        if not dropareas:
            return ""
        spaces = " ".join(dropareas)
        return f"{{{spaces}}}"

    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']
        users_mode = kwargs['users']
        groups_mode = kwargs['groups']
        builds_mode = kwargs['builds']
        staffs_mode = kwargs['staffs']
        verbose = kwargs['verbose']
        podman_flag = kwargs['podman']

        if users_mode:
            list_courses_users(patterns, verbose)
            return

        if groups_mode:
            list_courses_groups(patterns, verbose)
            return

        if builds_mode:
            list_courses_builds(patterns, verbose)
            return

        if staffs_mode:
            list_courses_staffs(patterns, verbose)
            return

        def groups(cd):
            return " + ".join(group.name for group in cd.registered_groups.all())

        def show_course(cd, max_name, max_image, max_groups, max_droparea):
            col_name = f"{max_name+1}s"
            col_groups = f"{max_groups+1}s"
            autopull = "[AP]" if cd.autopull else ""
            autobuild = "[AB]" if cd.autobuild else ""
            archived = "[AR]" if cd.archived else ""
            flags = "".join([x for x in (autopull, autobuild, archived) if x])
            flags = f"{flags:13s}"
            dropareas = self.dropareas(cd)
            droparea_part = f"{dropareas:{max_droparea+1}}"
            hash_part = f"{cd.current_hash():9s}"
            groups_part = f"{groups(cd):{col_groups}}"
            image = cd.image

            line = f"{cd.coursename:{col_name}}"
            if verbose == 0:
                return line

            image_exists = None
            if podman_flag:
                import podman
                PODMAN_URL = "unix:///run/podman/podman.sock"
                with podman.PodmanClient(base_url=PODMAN_URL) as podman_api:
                    image_exists = podman_api.images.exists(cd.image)
                warning = "!" if not image_exists else " "
                image = f"{warning}{image}{warning}"
                # we may have 2 more characters in the image part
                max_image += 2
            col_image = f"{max_image+1}s"

            image_part = f"{image:{col_image}}"
            line += image_part
            line += flags
            if verbose == 1:
                return line
            line += droparea_part
            line += hash_part
            line += groups_part
            if verbose >= 3:
                line += f"{cd.nb_registered_users():>3}u "
                line += f"{cd.giturl}"
                line += f"@{cd.current_branch()}"
            if image_exists is False:
                escape = chr(27)
                line = f"{escape}[1m{escape}[31m{line}{escape}[0m"
            return line


        selected = sorted(CourseDir.courses_by_patterns(patterns))

        max_name = max((len(cd.coursename) for cd in selected), default=4)
        max_image = max((len(cd.image) for cd in selected), default=4)
        max_groups = max((len(groups(cd)) for cd in selected), default=3)
        max_droparea = max((len(self.dropareas(cd)) for cd in selected), default=1)
        for coursedir in selected:
            print(show_course(coursedir, max_name, max_image, max_groups, max_droparea))
        return 0
