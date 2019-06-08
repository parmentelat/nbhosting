#!/usr/bin/env python3


settings_path = "nbh_main.settings"

def main():
    import sys
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_path)
    django.setup()
    from django.core.management import execute_from_command_line
    # allow to use subcommands with dashes
    # but allow e.g. --help to pass through as-is
    if len(sys.argv) >= 2:
        if not sys.argv[1].startswith('-'):
            sys.argv[1] = sys.argv[1].replace('-', '_')
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
