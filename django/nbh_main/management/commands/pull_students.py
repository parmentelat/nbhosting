# pylint: disable=no-member

from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand

from nbh_main.settings import logger, NBHROOT

from nbhosting.courses.model_course import CourseDir

from nbhosting.matching import matching_policy

class Command(BaseCommand):

    help = """
    This command performs git pull en masse in the students' workspaces.
    Being a classroom-oriented feature, only registered users are taken into account.
    
    **Action in the course area:**
    For all courses concerned, it will first git-pull in the course's
    main git repo, unless (*) the course does not have autpull enabled, 
    or (*) the -k option is mentioned.
    
    **Action in the students areas:**
    The -s, -u and -a options allow to focus on some students only; -s is cumulative.

    Without the -p option, it simply checks that the students workspaces are
    on the same commit as the course's main git repo; with the -p option, it will first 
    perform a git-pull in the selected students' workspaces.
    
    **Matching:**
    For selecting courses or students, you can use patterns with the following 
    policy: 'foo' means all courses whose name contains 'foo'; 
    '=foo' means the course whose name is 'foo'; '*foo' means all courses whose 
    name ends in 'foo'; so 'foo' is equivalent to '*foo*'. 
    Same rules apply to students.
    
    example: `nbh-manage pull-students` to update all courses and make a global check

    example: `nbh-manage pull-students -kp mines` to avoid git-pulling, 
    and pull from all students who have a workspace in a course named in '*mines*' 
    
    example: `nbh-manage pull-students -kpa mines` on the same courses, 
    skip pulling in the course's area, but pull for all staff members.

    """

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser


    def add_arguments(self, parser):
        parser.add_argument("courses", nargs='*', type=str, help="course patterns")

        parser.add_argument("-k", "--skip-pull",
                            action='store_false', dest='pull_course', default=True,
                            help="skip doing git pull in the courses area")

        parser.add_argument("-p", "--pull", action='store_true', default=False,
                            help="perform git pull in the students' workspaces")
        
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

    def handle(self, *args, **kwargs):

        courses = kwargs['courses']
        staff_selector = None
        if kwargs['students_only']:
            staff_selector = {'student'}
        elif kwargs['staff_only']:
            staff_selector = {'staff'}
        else:
            staff_selector = {'staff', 'student'}
        do_pull = kwargs['pull']
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
                                   courses):
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
                    do_pull=do_pull,
                    quiet_mode=quiet_mode)
        return 0
