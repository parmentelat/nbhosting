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

import asyncio
import re
import time

import podman
podman_url = "unix://localhost/run/podman/podman.sock"

from nbhosting.stats.monitor import MonitoredJupyter, CourseFigures


loop = asyncio.get_event_loop()


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument("patterns", nargs='*')
        args = parser.parse_args()
    
    def handle(self, *args, **kwargs):

        patterns = kwargs['patterns']
        selection = not not patterns
        def in_scope(container):
            if not patterns:
                return True
            else:
                return any(re.match(pattern, container['Names'][0])
                        for pattern in patterns)

        ban = 10 * '*'
        with podman.ApiConnection(podman_url) as api:
            containers = podman.containers.list_containers(api)
            #print(containers[0])
            all_running = [ c for c in containers if c['State'] == 'running']
            selected_running = [c for c in all_running if in_scope(c)]
            all_idle = [ c for c in containers if c['State'] != 'running']
            selected_idle = [c for c in all_idle if in_scope(c)]

            if selection:
                print(ban, f"{len(selected_idle)}/{len(all_idle)}"
                    f" selected/total idle containers")
                print(ban, f"{len(selected_running)}/{len(all_running)}"
                    f" selected/total running containers")
            else:
                print(ban, f"{len(selected_idle)} total idle containers")
                print(ban, f"{len(selected_running)} total running containers")
            
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
            width = max(len(c.name) for c in running_monitoreds)
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
