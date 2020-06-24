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
        parser.add_argument("-i", "--idle", default=True, action='store_false')
        parser.add_argument("patterns", nargs='*')
        # args = parser.parse_args()
    

    def in_scope(self, container_or_monitored):
        """
        Parameter can be either a container (a dict as returned by podman)
        or a MonitoredJupyter object
        """
        if not self.patterns:
            return True
        else:
            name = (container_or_monitored['Names'][0] 
                    if (isinstance(container_or_monitored, dict)
                        and 'Names' in container_or_monitored)
                    else container_or_monitored.name)
            return any(re.match(pattern, name)
                    for pattern in self.patterns)


    BANNER = 8 * '*'

    def run_once(self, show_details, show_idle=False):
        try:
            self._run_once(show_details, show_idle)
        except Exception as exc:
            import traceback
            print(self.BANNER, f"OOPS {type(exc)}, {exc}",
                  end="\n" if show_details else "")
            traceback.print_exc()
    
    def _run_once(self, show_details, show_idle):
        """
        The total number of containers is split like this:
        * total = stopped + running
          running = idle (0 kernels) + active (>= 1 kernel)
        
        Parameters:
          show_details: if True, print one line per container 
            with last activity and # of kernels
          show_idle: if True, compute the number of containers
            that have no kernel
        """
        
        with podman.ApiConnection(podman_url) as api:
            containers = podman.containers.list_containers(api)

        all_running = [ c for c in containers if c['State'] == 'running']
        all_stopped = [ c for c in containers if c['State'] != 'running']

        def monitored(container):
            name = container['Names'][0]
            course, student = name.split('-x-')
            # create one figures instance per container
            figures = CourseFigures()
            return MonitoredJupyter(container, course, student, figures, None)
            
        running_monitoreds = [monitored(container) for container in all_running]

        if show_details or show_idle:
            # probe them to fill las_activity and number_kernels
            futures = [mon.count_running_kernels() for mon in running_monitoreds]
            #loop.run_until_complete(asyncio.gather(*futures))
            for future in futures:
                loop.run_until_complete(future)

        if show_details:

            running_monitoreds.sort(key=lambda mon: mon.last_activity or 0, reverse=True)
            now = time.time()
            width = max((len(c.name) for c in running_monitoreds), default=10)
            for index, mon in enumerate(running_monitoreds, 1):
                if mon.nb_kernels:
                    # xxx this somehow shows up UTC
                    # maybe it simply needs USE_TZ = True in the django settings
                    la = mon.last_activity_human()
                    ellapsed = int(now - mon.last_activity) // 60
                    print(f"{index:<3d}{mon.name:>{width}s} [{mon.nb_kernels:>2d}k] "
                            f"last active {la} - {ellapsed:>3d} min ago")
                else:
                    display = '?' if mon.nb_kernels is None else 0
                    print(f"{index:<3d}{mon.name:>{width}s} [-{display}-] ")

        if show_details:
            ban = self.now()
            sep = "\n"
        else:
            ban = sep = ""
            
        def print_line(stopped, monitoreds, msg):
            if show_idle:
                nb_stopped = len(stopped)
                nb_idle = sum((mon.nb_kernels == 0 or mon.nb_kernels is None)
                              for mon in monitoreds)
                nb_active = len(monitoreds) - nb_idle
                total_kernels = sum((mon.nb_kernels or 0) for mon in monitoreds)
                total = nb_stopped + nb_idle + nb_active
                print(self.now(),
                      f"{msg} {nb_stopped} stopped + "
                      f"({nb_idle} idle + {nb_active} active) "
                      f"= {total} containers"
                      f" with {total_kernels} kernels", end=sep)
            else:
                nb_stopped = len(stopped)
                nb_running = len(monitoreds)
                total = nb_stopped + nb_running
                print(self.now(),
                      f"{msg} {nb_stopped} stopped + "
                      f"{nb_running} running = {total} "
                      f"containers", end=sep)
                
                
        print_line(all_stopped, running_monitoreds, "ALL")
        if self.patterns:
            selected_stopped = [c for c in all_stopped if self.in_scope(c)]
            selected_running = [mon for mon in running_monitoreds 
                                if self.in_scope(mon)]
            if self.continuous:
                print()
            print_line(selected_stopped, selected_running, "SEL")
            
    def now(self):
        return f"{datetime.now():%H:%M:%S}"

    def handle(self, *args, **kwargs):

        self.patterns = kwargs['patterns']
        self.period = kwargs['period']
        self.continuous = kwargs['continuous']
        self.idle = kwargs['idle']
        # using -p implies -c
        if self.period != DEFAULT_PERIOD:
            self.continuous = True


        if not self.continuous:
            self.run_once(show_details=True, show_idle=self.idle)
        else:
            try:
                while True:
                    self.run_once(show_details=False, show_idle=self.idle)
                    print(f" {self.now()} (w {self.period:d}s)", end=""); 
                    sys.stdout.flush()
                    time.sleep(self.period)
                    print("")
            except KeyboardInterrupt:
                print("bye")

