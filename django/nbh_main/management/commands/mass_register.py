# pylint: disable = c0111, w1203

"""
input file format:
* one user per line
* each line has one email and optional fields, see OPTIONS below
"""

import random
import string
import logging

import re

# keep it simple, we expect a localhost sendmail service
import smtplib

from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group
from django.template.loader import get_template, TemplateDoesNotExist

from nbh_main.sitesettings import server_name, server_mode


logging.basicConfig(level=logging.INFO)


OPTIONS = {'username', 'password', 'first_name', 'last_name'}
PASSWORD_CHARS = string.ascii_letters + string.digits


# how to compute defaults from an email
# when that's the only info we have for a user
def default_username(email):
    left, *_ = email.split('@')
    return left

def default_password(_email):
    return "".join(random.choice(PASSWORD_CHARS) for i in range(12))

def _default_name(email, zero_or_one, default):
    "0 is for first name and 1 for last name"
    left, *_ = email.split('@')
    try:
        return left.split('.')[zero_or_one]
    except (ValueError, IndexError):
        return default

def default_first_name(email):
    return _default_name(email, 0, "unknown-first-name")
def default_last_name(email):
    return _default_name(email, 1, "unknown-last-name")


# a range of valid chars with letters, digits, - . _
CRANGE = r"[-.\w]"
# same with spaces
CRANGESP = r"[-.\w ']"
SP = "[ \t]"

EMAIL = rf"{CRANGE}+@{CRANGE}+"
ATTRIBUTE = "[a-z_]+"
VALUE = rf'({CRANGE}+|\"{CRANGESP}+\")'
PAIR = rf"{ATTRIBUTE}={VALUE}"
QPAIR = rf"(?P<attribute>{ATTRIBUTE})=(?P<value>{VALUE})"

LINE = rf"(?P<email>{EMAIL})\W+(?P<attributes>({PAIR}{SP}*)*)"

RE_LINE = re.compile(LINE)
RE_PAIR = re.compile(QPAIR)

def parse(input_filename):
    # we first parse the whole file and do various checks
    # then ask for confirmation and do it all at once at the end
    todos = []
    parse_error = False
    with open(input_filename) as input_file:
        for lineno, line in enumerate(input_file, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                match = RE_LINE.match(line)
                email, attributes = match.group('email'), match.group('attributes')
                todo = dict(email=email, lineno=lineno)
                while attributes:
                    m_pair = RE_PAIR.search(attributes)
                    if not m_pair:
                        # end of line - exit while loop
                        continue
                    attribute = m_pair.group('attribute')
                    value = m_pair.group('value')
                    if value[0] == '"' and value[-1] == '"':
                        value = value[1:-1]
                    attributes = attributes[m_pair.end():]
                    if attribute not in OPTIONS:
                        raise ValueError(f"no such attribute {attribute}")
                    todo[attribute] = value
                for attribute in OPTIONS:
                    if attribute in todo:
                        continue
                    default_function = globals()[f"default_{attribute}"]
                    todo[attribute] = default_function(email)
                todos.append(todo)
            except Exception as exc:                    # pylint: disable=w0703
                logging.error(f"{lineno}:{line}:{exc}")
                parse_error = True
    return todos, parse_error


def filter_todos(todos):
    """
    filter todos and returns 2 lists
    * already existing and consistent
    * new accounts altogether
    some that exhibit partial conflicts (already existing,
    but with email/username mismatching)
    are discarded
    """
    olds = []
    news = []
    for todo in todos:
        lineno = todo['lineno']
        email = todo['email']
        username = todo['username']
        u_email = User.objects.filter(email=email)
        u_username = User.objects.filter(username=username)
        if u_email or u_username:
            u_both = User.objects.filter(email=email, username=username)
            if u_both:
                olds.append(todo)
            else:
                logging.warning(
                    f"line {lineno}, ignoring ambiguous pre-existing entry\n"
                    f"email and username mismatch")
        else:
            news.append(todo)
    return olds, news

def display_todo(todo):
    return f"{todo['email']} on line {todo['lineno']} ({todo['first_name']} {todo['last_name']})"


MAIL_SHOWED = False

def mail_user(todo, template, dry_run):
    sender = f"no-reply@{server_name}"
    receiver = todo['email']
    # subject should be filled in template in the first line
    # starting with Subject:
    subject = None
    visible_vars = todo.copy()
    visible_vars.update(dict(
        server_name=server_name,
        web_address=f"{server_mode}://{server_name}/",
        ))
    contents = template.render(visible_vars)

    lines = contents.split("\n")
    subject = lines[0].replace("Subject:", "")
    contents = "\n".join(lines[1:])
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver

    part = MIMEText(contents, "plain")
    message.attach(part)

    if dry_run:
        global MAIL_SHOWED
        if not MAIL_SHOWED:
            logging.info(f"sender={sender}, receiver={receiver}, subject={subject}")
            logging.info(message.as_string())
            MAIL_SHOWED = True
        return
    with smtplib.SMTP('localhost') as mailer:
        mailer.sendmail(sender, receiver, message.as_string())


def create_users(todos, template, dry_run):
    done = []
    for todo in todos:
        try:
            if dry_run:
                logging.info(f"Would create {todo}")
            else:
                _user = User.objects.create_user(
                    username=todo['username'],
                    email=todo['email'],
                    first_name=todo['first_name'],
                    last_name=todo['last_name'],
                    password=todo['password'],
                    )
            mail_user(todo, template, dry_run)
            done.append(todo)
        except Exception as exc:
            lineno = todo['lineno']
            logging.exception(f"{lineno}, "
                              f"failed to create user: {exc}")
    return done


def open_and_check_template(template_filename):
    try:
        template = get_template(template_filename)
    except TemplateDoesNotExist as exc:
        logging.error(f"could not load template {template_filename}")
        logging.error(f"tried these: {exc.tried}")
        exit(1)
    # check for the Subject line
    void = template.render({})
    if not void.startswith("Subject:"):
        logging.error("template must start with a Subject: line")
        exit(1)
    return template


def create_group_if_needed(groupname):
    if not groupname:
        return
    group, _created = Group.objects.get_or_create(name=groupname)
    return group


def add_todos_in_group(todos, group, dry_run):
    for todo in todos:
        username = todo['username']
        user = User.objects.get(username=username)
        if dry_run:
            print(f"would add user {username} in group {group.name}")
        else:
            group.user_set.add(user)


def mass_register(input_filename, template_filename, groupname, long_output, dry_run):
    template = open_and_check_template(template_filename)
    todos, parse_error = parse(input_filename)
    logging.info(f"parsed {len(todos)} entries, checking for news")
    olds, news = filter_todos(todos)
    logging.info(f"found  {len(olds)} old + {len(news)} new entries")
    if long_output:
        for old in olds:
            print("OLD", display_todo(old))
        print("NEW entries")
        for new in news:
            print("NEW", display_todo(new))
    
    proceed = (len(olds) + len(news)) == len(todos)
    if parse_error or not proceed:
        go_ahead = False
        prompt = "OK y/[n] ? "
    else:
        go_ahead = True
        prompt = "OK [y]/n ? "

    answer = input(prompt).lower()
    if not answer:
        # use go_ahead as computer earlier
        pass
    else:
        go_ahead = answer[0] == 'y'
    if not go_ahead:
        logging.info("no worries, bye")
        return
    done = create_users(news, template, dry_run)
    if dry_run:
        logging.info(f"{len(done)} accounts NOT CREATED (dry-run)")
    else:
        logging.info(f"{len(done)} new accounts created")

    group = create_group_if_needed(groupname)
    print(f"group={group}")
    if group:
        add_todos_in_group(olds + news, group, dry_run)


class Command(BaseCommand):

    help = """%(prog)s : performs users mass registration

    ----
    main input is a text file with one line per user

    * comments are supported when line starts with a #
    * non-comment lines:
      * must provide an email-address
      * and may specify any of the following,
        that are otherwise computed from the mail address

        * username
        * password
        * first_name
        * last_name

    e.g.
    jean.dupont@free.fr username=jean_dupont

    ----
    template file is used to write the email that all newly created users
    will receive
    it should be located like other django template files

    available in mail template (between {{}}):

    * username
    * password
    * email
    * first_name
    * last_name
    * server_name
    * web_address

    ----
    group management
    
    if the -g option is present, all the accounts present in 
    the input file will be added to that group, which is created
    if needed.
    
    It is safe to run mass-register several times on a given input file,
    as only unexisting accounts are created; tis is useful too existing 
    accounts in a group.    
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry-run", default=False, action='store_true',
            help="just pretends")
        parser.add_argument(
            "-l", "--long", dest='long_output', default=False, action='store_true',
            help="long (verbose) output"
        )
        parser.add_argument(
            "-t", "--template", default="mass-register.mail",
            help="filename for mail body template - **searched** "
                 "together with regular django templates")
        parser.add_argument(
            "-g", "--group", default=None, action='store',
            help="name of a group where all users are added; "
                 "group is created if needed; "
                 "users are added in group even if user was already created")
        parser.add_argument(
            "filename", nargs=1, help="input file name")

    def handle(self, *args, **kwargs):
        mass_register(kwargs['filename'][0],
                      kwargs['template'],
                      kwargs['group'],
                      kwargs['long_output'],
                      kwargs['dry_run'],
                      )