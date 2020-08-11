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
    python-slides python3-s2 
    """

    def add_arguments(self, parser):
        parser.add_argument("patterns", nargs='*', type=str)
        parser.add_argument(
            "-l", "--list", action="count", default=0, dest="verbose",
            help=("Give more output. Option is additive, and can be used up to 2 "
                  "times."),
        )

    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']
        verbose = kwargs['verbose']

        def show_course(cd, max_name, max_image):
            autopull = "[AP]" if cd.autopull else ""
            archived = "[AR]" if cd.archived else ""
            col1 = f"{max_name+1}s"
            col2 = f"{max_image+1}s"
            hash = f"{cd.current_hash():9s}"
            line = f"{cd.coursename:{col1}}"
            if verbose == 1:
                line += f"{cd.image:{col2}}"
                line += f"{autopull:5s}"
                line += f"{hash}"
                line += f"{cd.giturl}"
            else:
                groups = cd.registered_groups.all()
                groupnames = " + ".join(group.name for group in groups)
                line += f"{cd.image:{col2}}"
                line += f"{autopull:5s}"
                line += f"{archived:5s}"
                line += f"{hash}"
                line += f"RGS=[{groupnames}]"
                line += f"{cd.giturl}"
            print(line)
                

        all_coursedirs = sorted(
            CourseDir.objects.all(),
            key=lambda coursedir: coursedir.coursename)
        max_name = max((len(cd.coursename) for cd in all_coursedirs), default=4)
        max_image = max((len(cd.image) for cd in all_coursedirs), default=4)
        for coursedir in all_coursedirs:
            name = coursedir.coursename
            if not patterns:
                show_course(coursedir, max_name, max_image)
            else:
                for pattern in patterns:
                    if pattern == '*' or pattern in name:
                        show_course(coursedir, max_name, max_image)
                        break
        return 0
