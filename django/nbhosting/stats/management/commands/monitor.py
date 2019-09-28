#!/usr/bin/env python3

# pylint: disable=c0111

from django.core.management.base import BaseCommand

from nbhosting.stats.monitor import Monitor

DEFAULT_PERIOD = 10
DEFAULT_IDLE = 30

class Command(BaseCommand):

    def add_arguments(self, parser):
        # default was 2 hours with the jupyter-v4 strategy,
        # which was based on the last time a notebook was opened
        # with jupyter-v5 we can now really apply a timeout
        parser.add_argument(
            "-p", "--period", default=DEFAULT_PERIOD, type=int,
            help="monitor period in minutes - how often are checks performed "
                 f"(default={DEFAULT_PERIOD})")
        parser.add_argument(
            "-i", "--idle", default=DEFAULT_IDLE, type=int, dest='idle',
            help="timeout in minutes - kill containers idle more than that "
                 f"(default={DEFAULT_IDLE})")
        parser.add_argument(
            "-u", "--unused", default=15, type=int, dest='unused',
            help="timeout in days - remove containers unused more than that")
        parser.add_argument(
            "-d", "--debug", action='store_true', default=False)


    def handle(self, *args, **kwargs):
        monitor = Monitor(
            period=60 * kwargs['period'],
            idle=60 * kwargs['idle'],
            unused=24*3600 * kwargs['unused'],
            debug=kwargs['debug'])
        monitor.run_forever()
