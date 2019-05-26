#!/usr/bin/env python3

import os
import sys

settings_path = "nbh_main.settings"

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
    # allow to use subcommands with dashes
    # but allow e.g. --help to pass through as-is
    if len(sys.argv) >= 2:
        if not sys.argv[1].startswith('-'):
            sys.argv[1] = sys.argv[1].replace('-', '_')
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
