# pylint: disable = c0111, w1203

"""
input file format:
* one user per line
* each line has one email and optional fields, see OPTIONS below
"""

import random
import string
import logging
from pathlib import Path
import json

import re

# keep it simple, we expect a localhost sendmail service
import smtplib

import pandas as pd

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import get_template, TemplateDoesNotExist

from nbh_main.sitesettings import server_name, server_mode


logging.basicConfig(level=logging.INFO)

MANDATORY = ['email']
OPTIONS = ['username', 'first_name', 'last_name', 'password', ]
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
    for sep in ('.', '-', '_'):
        split = left.split(sep)
        if len(split) != 2:
            continue
        return split[zero_or_one]
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

# def save_todos_csv(todos, csv_filename: str):
#     df = pd.DataFrame(todos)
#     # keep only the relevant ones
#     # and put email first
#     to_save = sorted((set(MANDATORY) | set(OPTIONS)) & set(df.columns))
#     print(f"{to_save=}")
#     df.to_csv(csv_filename, columns=to_save, index=False)
#     print(f"(over)wrote {csv_filename}")

def parse(input_filename: str, long_output: bool):
    # we first parse the whole file and do various checks
    # then ask for confirmation and do it all at once at the end
    todos = []
    df = pd.read_csv(input_filename)
    # turns out my own install of Numbers stores csv that are ;-separated
    if 'email' not in df.columns:
        df = pd.read_csv(input_filename, sep=';')
        if 'email' not in df.columns:
            print("email field is mandatory ! (make sure to use ',' or ';' as a separator")
            exit(1)
    ALL = MANDATORY + OPTIONS
    for field in ALL:
        if field not in df.columns:
            if field == "password":
                # do not bothering this common case
                continue
            print(f"WARNING: supported field not provided {field}")
    for col in df.columns:
        if col not in ALL:
            print(f"WARNING, input has unknown/unsupported column {col} - will be ignored")
    keep = [x for x in df.columns if x in ALL]
    df = df[keep]
    # convert data from df into the original format that was a list of dicts
    todos = [s.to_dict() for i, s in df.iterrows()]
    # autofill data
    for todo in todos:
        email = todo['email']
        for attribute in OPTIONS:
            if attribute in todo and not pd.isnull(todo[attribute]):
                continue
            # missing slot:
            # locate function for auto-completion
            default_function = globals()[f"default_{attribute}"]
            # call it and store result
            todo[attribute] = default_function(email)
    return todos


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
        email = todo['email']
        username = todo['username']
        u_email = User.objects.filter(email=email)
        u_username = User.objects.filter(username=username)
        if len(todo['username']) >= 32:
            before = todo['username']
            todo['username'] = todo['username'][:31]
            logging.warning(f"name too long {before}\n"
                  f"       is truncated to {todo['username']}")
        if u_email or u_username:
            u_both = User.objects.filter(email=email, username=username)
            if u_both:
                olds.append(todo)
            else:
                logging.warning(
                    f"email {email}, ignoring ambiguous pre-existing entry\n"
                    f"email and username mismatch")
        else:
            news.append(todo)
    return olds, news

def display_todo(todo):
    return f"{todo['email']} ({todo['first_name']} {todo['last_name']})"


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


def create_users(todos, template, dry_run, skip_mail):
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
            if not skip_mail:
                mail_user(todo, template, dry_run)
            done.append(todo)
        except Exception as exc:
            email = todo['email']
            logging.exception(f"{email}, "
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
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            logging.warning(f"not existing yet - skipping addition of {username} in group {group}")
            continue
        if dry_run:
            print(f"would add user {username} in group {group.name}")
        else:
            group.user_set.add(user)


def mass_register(input_filename, template_filename, groupname, long_output, dry_run, skip_mail):
    template = open_and_check_template(template_filename)
    if input_filename.endswith(".input"):
        print("the .input format is no longer supported, use a .csv instead")
        exit(1)
    try:
        todos = parse(input_filename, long_output)
    except Exception as exc:
        logging.exception("bad input")
        exit(1)

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
    if not proceed:
        go_ahead = False
        prompt = "OK y/[n] ? "
    else:
        go_ahead = True
        prompt = "OK [y]/n ? "

    answer = input(prompt).lower()
    if not answer:
        # use go_ahead as computed earlier
        pass
    else:
        go_ahead = answer[0] == 'y'
    if not go_ahead:
        logging.info("no worries, bye")
        return
    done = create_users(news, template, dry_run, skip_mail)
    if dry_run:
        logging.info(f"{len(done)} accounts NOT CREATED (dry-run)")
    else:
        logging.info(f"{len(done)} new accounts created")

    group = create_group_if_needed(groupname)
    print(f"group={group}")
    if group:
        add_todos_in_group(olds + news, group, dry_run)

    return todos


def export_json(in_filename, todos, sponsor):
    print(f"in export_json: {len(todos)=}")
    # todo : configurable
    USERMODEL = 'student_teams.User'
    is_sponsor = sponsor
    is_student = not is_sponsor
    items = []
    for todo in todos:
        try:
            user = User.objects.get(email=todo['email'])
            fields = dict(first_name=user.first_name, last_name=user.last_name,
                        username=user.username, email=user.email,
                        password=user.password,
                        is_student=is_student, is_sponsor=is_sponsor)
            items.append(dict(model=USERMODEL, fields=fields))
            print("added one item to json")
        except:
            logging.warning(f"email {todo['email']} not yet known (dry-run ?)")
    out_filename = f"{in_filename}.json"
    with Path(out_filename).open('w') as writer:
        writer.write(json.dumps(items))
    print(f"{out_filename} created or overwritten")


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
    as only unexisting accounts are created; this is also useful to add existing
    accounts in a group.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--dry-run", default=False, action='store_true',
            help="just pretends")
        parser.add_argument(
            "-s", "--skip-mail", default=False, action='store_true',
            help="do create users, but do not send mails")
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
            "-e", "--export-json", default=False, action='store_true',
            help="generate a JSON-encoded file to export"
                 " these users to another django app")
        parser.add_argument(
            "-o", "--sponsor", default=False, action='store_true',
            help="useful with --export-json, when exported entities"
                 " need to be marked as sponsors instead of regular students")
        parser.add_argument(
            "filename", nargs=1, help="input file name")

    def handle(self, *args, **kwargs):
        todos = mass_register(kwargs['filename'][0],
                              kwargs['template'],
                              kwargs['group'],
                              kwargs['long_output'],
                              kwargs['dry_run'],
                              kwargs['skip_mail'],
                              )
        if kwargs['export_json']:
            export_json(kwargs['filename'][0], todos, kwargs['sponsor'])
