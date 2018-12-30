#!/usr/bin/env python3
import os
import sys

settings_path = "nbhosting.main.settings"

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
        if '__' in symbol or 'SECRET' in symbol:
            continue
        if isinstance(value, str):
            print(f"{symbol}='{value}'")
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            # expose list of strings as a bash array
            between_quote = lambda x: f"'{x}'"
            bash_repr = " ".join(between_quote(v) for v in value)
            print(f"{symbol}=({bash_repr})")

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
