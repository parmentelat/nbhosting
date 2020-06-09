"""
a rough utility to count 
. known containers
. running containers
. kernels per (running) container
. last activity

it is overlapping with monitor a little, 
but with a troubleshooting-oriented display
"""

from django.core.management.base import BaseCommand

import sys
import time
from datetime import datetime
import re
import asyncio

import podman
podman_url = "unix://localhost/run/podman/podman.sock"

from nbhosting.stats.monitor import MonitoredJupyter, CourseFigures


loop = asyncio.get_event_loop()

DEFAULT_PERIOD = 1

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("-c", "--continuous", default=False, action='store_true')
        parser.add_argument("-p", "--period", default=DEFAULT_PERIOD, type=int)
        parser.add_argument("patterns", nargs='*')
        args = parser.parse_args()
    
    def in_scope(self, container):
        if not self.patterns:
            return True
        else:
            return any(re.match(pattern, container['Names'][0])
                    for pattern in self.patterns)


    BANNER = 10 * '*'

    def one_time(self, details):
        try:
            self._one_time(details)
        except Exception as exc:
            print(self.BANNER, f"OOPS {type(exc)}, {exc}",
                  end="\n" if details else "")
    
    def _one_time(self, details):
        
        patterns = self.patterns

        if details:
            ban = self.BANNER
            sep = "\n"
        else:
            ban = sep = ""
        with podman.ApiConnection(podman_url) as api:
            containers = podman.containers.list_containers(api)
            #print(containers[0])
            all_running = [ c for c in containers if c['State'] == 'running']
            selected_running = [c for c in all_running if self.in_scope(c)]
            all_idle = [ c for c in containers if c['State'] != 'running']
            selected_idle = [c for c in all_idle if self.in_scope(c)]

            if not self.patterns:
                print(ban, f"total {len(selected_running)}/{len(selected_idle)} "
                           f"running/idle containers", end=sep)
            else:
                print(ban, f"{len(selected_running)}/{len(all_running)}"
                           f" selected/total running containers", end=sep)
                print(ban, f"{len(selected_idle)}/{len(all_idle)}"
                           f" selected/total idle containers", end=sep)
            
            if not details:
                return

            def monitored(container):
                name = container['Names'][0]
                course, student = name.split('-x-')
                # create one figures instance per container
                figures = CourseFigures()
                mon = MonitoredJupyter(container, course, student, figures, None)
                loop.run_until_complete(mon.count_running_kernels())
                nb_kernels = figures.running_kernels
                return mon
                
            running_monitoreds = [monitored(container) for container in selected_running]
            idle_monitoreds = [monitored(container) for container in selected_idle]
            running_monitoreds.sort(key=lambda mon: mon.last_activity or 0, reverse=True)
            now = time.time()
            width = max((len(c.name) for c in running_monitoreds), default=10)
            for mon in running_monitoreds:
                if mon.nb_kernels:
                    # xxx this somehow shows up UTC
                    # maybe it simply needs USE_TZ = True in the django settings
                    la = mon.last_activity_human()
                    ellapsed = int(now - mon.last_activity) // 60
                    print(f"{mon.name:>{width}s} [{mon.nb_kernels:>2d}k] "
                        f"last active {la} - {ellapsed:>3d} min ago")
                else:
                    print(f"{mon.name:>{width}s} [-0-] ")

    def handle(self, *args, **kwargs):

        self.patterns = kwargs['patterns']
        self.period = kwargs['period']
        self.continuous = kwargs['continuous']
        # using -p implies -c
        if self.period != DEFAULT_PERIOD:
            self.continuous = True


        if not self.continuous:
            self.one_time(details=True)
        else:
            try:
                while True:
                    print(f"{datetime.now():%H:%M:%S} ", end="")
                    sys.stdout.flush()
                    self.one_time(details=False)
                    print(f" {datetime.now():%H:%M:%S} (w {self.period:d}s)", end=""); 
                    sys.stdout.flush()
                    time.sleep(self.period)
                    print("")
            except KeyboardInterrupt:
                print("bye")

