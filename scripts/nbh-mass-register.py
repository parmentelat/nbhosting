#!/usr/bin/env python3

# pylint: disable = c0111, w1203

"""
input file format:
* one user per line
* each line has one email and optional fields, see OPTIONS below
"""

import random
import string
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging

# keep it simple, we expect a localhost sendmail service
import smtplib

# set and export django settings module
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nbhosting.main.settings")

import django
django.setup()


from django.contrib.auth.models import User
from django.template.loader import get_template, TemplateDoesNotExist

from nbhosting.main.sitesettings import server_name, server_mode


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
                email, *options = line.split()
                todo = dict(email=email, lineno=lineno)
                for option in options:
                    optname, value = option.split('=')
                    if optname not in OPTIONS:
                        raise ValueError(f"no such option {optname}")
                    todo[optname] = value
                for optname in OPTIONS:
                    if optname in todo:
                        continue
                    default_function = globals()[f"default_{optname}"]
                    todo[optname] = default_function(email)
                todos.append(todo)
            except Exception as exc:                    # pylint: disable=w0703
                logging.error(f"{lineno}:{line}:{exc}")
                parse_error = True
    return todos, parse_error


def _spot_conflicting(field, field_value):
    kwds = {field: field_value}
    return User.objects.filter(**kwds)


def check(todos):
    checked = []
    for todo in todos:
        lineno = todo['lineno']
        email = todo['email']
        username = todo['username']
        # we have no 'I forgot my password' feature yet
        if _spot_conflicting('email', email):
            logging.warning(f"line {lineno}, "
                            f"email {email} already registered, ignoring")
            continue
        if _spot_conflicting('username', username):
            logging.warning(
                f"line {lineno}, "
                f"username {username} already registered, pick another")
            continue
        checked.append(todo)
    return checked


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
        logging.exception(f"could not load template template_filename")
        logging.info(exc.tried)
        exit(1)
    # check for the Subject line
    void = template.render({})
    if not void.startswith("Subject:"):
        logging.error("template must start with a Subject: line")
        exit(1)
    return template


def mass_register(input_filename, template_filename, dry_run):
    template = open_and_check_template(template_filename)
    todos, parse_error = parse(input_filename)
    logging.info(f"parsed {len(todos)} entries, checking")
    checked = check(todos)
    logging.info(f"found {len(checked)} new entries to be created")
    if not parse_error and (len(todos) == len(checked)):
        go_ahead = True
        prompt = "OK [y]/n ? "
    else:
        go_ahead = False
        prompt = "OK y/[n] ? "
    answer = input(prompt).lower()
    if not answer:
        # use go_ahead as computer earlier
        pass
    else:
        go_ahead = answer[0] == 'y'
    if not go_ahead:
        logging.info("no worries, bye")
        return
    done = create_users(checked, template, dry_run)
    if not dry_run:
        logging.info(f"{len(done)} new accounts created")
    else:
        logging.info(f"{len(done)} accounts NOT CREATED (dry-run)")


USAGE = """%(prog)s : performs users mass registration

----
main input is a text file with one line per user

* comments are supported when line starts with a #
* non-comment lines:
  * must provide an email-address
  * and my specify any of the following, that

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

"""

def main():
    parser = ArgumentParser(usage=USAGE,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--dry-run", default=False, action='store_true',
                        help="just pretends")
    parser.add_argument("-t", "--template", default="mass-register.mail",
                        help="filename for mail body template - **searched** "
                             "together with regular django templates")
    parser.add_argument("filename", nargs='?', default="mass-register.input",
                        help="input file name")
    args = parser.parse_args()
    mass_register(args.filename, args.template, args.dry_run)


main()
