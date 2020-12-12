# pylint: disable=c0111, r0201, w0613, w1203, w0106

import os

from django.core.management.base import BaseCommand

from nbhosting.courses.model_course import CourseDir

from nbh_main.settings import logger, NBHROOT

class Command(BaseCommand):

    help = """
    this command list known courses

    without argument it lists all courses; with arguments
    it lists all course whose name contains any of the tokens

    example: nbh-manage courses-list python bio

    could output: bioinfo mines-python-primer
    python-slides python-mooc
    """

    def add_arguments(self, parser):
        parser.add_argument("patterns", nargs='*', type=str)
        parser.add_argument(
            "-l", "--list", action="count", default=0,
            help=("Give more output. Option is additive, and can be used up to 2 "
                  "times."),
        )

    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']
        list_flag = kwargs['list']

        def groups(cd):
            return " + ".join(group.name for group in cd.registered_groups.all())

        def show_course(cd, max_name, max_image, max_groups):
            col_name = f"{max_name+1}s"
            col_groups = f"{max_groups+1}s"
            autopull = "[AP]" if cd.autopull else ""
            archived = "[AR]" if cd.archived else ""
            flags = "".join([x for x in (autopull, archived) if x])
            flags = f"{flags:9s}"
            hash_part = f"{cd.current_hash():9s}"
            groups_part = f"{groups(cd):{col_groups}}"
            image = cd.image

            line = f"{cd.coursename:{col_name}}"
            if list_flag == 0:
                return line

            image_exists = None
            if list_flag >= 3:
                import podman
                podman_url = "unix://localhost/run/podman/podman.sock"
                with podman.ApiConnection(podman_url) as podman_api:
                    image_exists = podman.images.image_exists(podman_api, cd.image)
                warning = "!" if not image_exists else " "
                image = f"{warning}{image}{warning}"
                # we may have 2 more characters in the image part
                max_image += 2
            col_image = f"{max_image+1}s"

            image_part = f"{image:{col_image}}"
            line += image_part
            line += flags
            if list_flag == 1:
                return line
            line += hash_part
            line += groups_part
            line += f"{cd.giturl}"
            if image_exists is False:
                escape = chr(27)
                line = f"{escape}[1m{escape}[31m{line}{escape}[0m"
            return line


        all_coursedirs = sorted(
            CourseDir.objects.all(),
            key=lambda coursedir: coursedir.coursename)
        if not patterns:
            selected = all_coursedirs
        else:
            def is_matched(cd):
                return any((pattern == '*' or pattern in cd.coursename)
                           for pattern in patterns)
            selected = [cd for cd in all_coursedirs if is_matched(cd)]

        max_name = max((len(cd.coursename) for cd in selected), default=4)
        max_image = max((len(cd.image) for cd in selected), default=4)
        max_groups = max((len(groups(cd)) for cd in selected), default=3)
        for coursedir in selected:
            print(show_course(coursedir, max_name, max_image, max_groups))
        return 0
