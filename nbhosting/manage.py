#!/usr/bin/env python3

# pylint: disable=c0111, r1705

import os
import sys

settings_path = "nbhosting.main.settings"

# called by install.sh to produce sitesettings.sh

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

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_path)
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
    try:
        if sys.argv[1] == "list-siteconfig":
            list_siteconfig()
            exit(0)
        else:
            main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        main()
