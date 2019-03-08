#!/usr/bin/env python3

# pylint: disable=c0111, r1705

import os
import sys

settings_path = "nbhosting.main.settings"

# our home-cooked manage.py exposes more commands
# that are invoked from various shell scripts
# mostly to retrieve configuration options

# in particular
# called by install.sh to produce sitesettings.sh

our_custom_subcommands = {}
def custom_subcommand(command):
    shell_name = command.__name__.replace('_', '-')
    our_custom_subcommands[shell_name] = command
    return command

# we have to consider a special case for the frame_ancestors variable
# because the ultimate output is to read
# 'Content-Security-Policy': "frame-ancestors 'self' https://*.fun-mooc.fr ;",
# so quoting gets kinda tricky
def shell_escape(value):
    if "'" in value:
        return f'"{value}"'
    else:
        return f"'{value}'"

def expose_var_value(symbol, value):
    print(f"{symbol}={shell_escape(value)}")

def expose_var_values(symbol, values):
    # expose list of strings as a bash array
    bash_repr = " ".join(shell_escape(v) for v in values)
    print(f"{symbol}=({bash_repr})")


@custom_subcommand
def list_siteconfig():
    from importlib import import_module
    # importing the settings module manually
    steps = []
    for step in settings_path.split('.'):
        steps.append(step)
        path = '.'.join(steps)
        settings = import_module(path)
    for symbol in dir(settings.sitesettings):
        value = getattr(settings.sitesettings, symbol,
                        'undefined-in-sitesettings')
        # don't expose everything
        if '__' in symbol or 'SECRET' in symbol:
            continue
        if isinstance(value, str):
            expose_var_value(symbol, value)
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            expose_var_values(symbol, value)

@custom_subcommand
def expose_static_mappings(coursename):
    from nbhosting.courses.model_course import CourseDir
    coursedir = CourseDir(coursename)
    for static_mapping in coursedir.static_mappings:
        print(static_mapping.expose(coursedir))

@custom_subcommand
def expose_static_toplevels(coursename):
    from nbhosting.courses.model_course import CourseDir
    from nbhosting.courses.model_mapping import StaticMapping
    coursedir = CourseDir(coursename)
    toplevels = StaticMapping.static_toplevels(
        coursedir.static_mappings
    )
    for toplevel in toplevels:
        print(toplevel)

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_path)
    subcommand = sys.argv[1]
    if subcommand in our_custom_subcommands:
        args = sys.argv[2:]
        our_custom_subcommands[subcommand](*args)
        exit(0)
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
