# pylint: disable=no-member

from django.core.management.base import BaseCommand

from nbh_main.settings import logger, NBHROOT

from nbhosting.courses.model_course import CourseDir

from nbhosting.matching import matching_policy

class Command(BaseCommand):

    help = """
    this command performs git pull en masse in the students' workspaces
    
    for all courses concerned, it will first git-pull in the course's main git repo

    without the -p option it checks that all students workspaces are
    on the same commit as the course's main git repo; with the -p option, it will first 
    perform a git-pull in the selected students' workspaces
    
    example: nbh-manage pull-students -p -s '*.*' mines
    """

    def add_arguments(self, parser):
        parser.add_argument("course_patterns", nargs='*', type=str)
        parser.add_argument("-p", "--pull", action='store_true', default=False,
                            help="perform git pull in the students' workspaces")
        parser.add_argument("-r", "--reset", action='store_true', default=False,
                            help="perform git reset --hard in the "
                                 "students' workspaces before pulling")
        parser.add_argument("-s", "--student",
                            dest='students', action='append', default=[],
                            help="student patterns")
        parser.add_argument("-u", "--students-only",
                            action='store_true', default=False,
                            help="only students, exclude staff")
        parser.add_argument("-a", "--staff-only",
                            action='store_true', default=False,
                            help="only staff")
        parser.add_argument("-q", "--quiet", action='store_true', default=False,
                            help="run quietly, with fewer output messages")
        parser.add_argument("-k", "--skip-pull",
                            action='store_false', dest='pull_course', default=True,
                            help="skip doing git pull in the courses area")

    def handle(self, *args, **kwargs):

        course_patterns = kwargs['course_patterns']
        staff_selector = None
        if kwargs['students_only']:
            staff_selector = {'student'}
        elif kwargs['staff_only']:
            staff_selector = {'staff'}
        else:
            staff_selector = {'staff', 'student'}
        do_pull = kwargs['pull']
        do_reset = kwargs['reset']
        quiet_mode = kwargs['quiet']
        pull_course = kwargs['pull_course']

        def myprint(*args):
            print(*args, end='', flush=True)
        def myqprint(*args):
            if not quiet_mode:
                myprint(*args)

        all_coursedirs = sorted(
            CourseDir.objects.all(),
            key=lambda coursedir: coursedir.coursename)
        for coursedir in all_coursedirs:
            if not matching_policy(coursedir.coursename,
                                   course_patterns):
                continue
            myprint(f"{4*'='} {coursedir.coursename} ")
            if not coursedir.autopull:
                myqprint("AP=off ")
            elif not pull_course:
                myqprint("[skipping pull] ")
            else:
                myqprint("pulling.. ")
                coursedir.pull_from_git(silent=True)
            course_hash = coursedir.current_hash()
            myprint(f"is on hash {course_hash}")
            print()
            for user, workspace in coursedir.users_with_workspace(
                    user_patterns=kwargs['students'],
                    staff_selector=staff_selector):
                coursedir.update_user_workspace(
                    user, user_workspace=workspace, course_hash=course_hash,
                    do_pull=do_pull, do_reset=do_reset)
        return 0
