import os

from django.core.management.base import BaseCommand

# pylint: disable=c0111, r1705

"""
this management command is used by the installation script

it extracts information stored in sitesettings.py and exposes it in
a shell source-able format, so that these values are available to
the installation shell script
"""



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

def expose_var_number(symbol, value):
    print(f"{symbol}={value}")

def expose_var_values(symbol, values):
    # expose list of strings as a bash array
    bash_repr = " ".join(shell_escape(v) for v in values)
    print(f"{symbol}=({bash_repr})")

class Command(BaseCommand):
    help = 'create configuration file for bash from local settings - used by install.sh'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        from importlib import import_module
        # importing the settings module manually
        steps = []
        settings_path = os.environ["DJANGO_SETTINGS_MODULE"]
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
            elif isinstance(value, (int, float)):
                expose_var_number(symbol, value)
            elif isinstance(value, list) and all(isinstance(v, str) for v in value):
                expose_var_values(symbol, value)
