import socket
import traceback

import docker

#
# a first naive implementation of port allocation would just find a free port in the OS
# however, this needs improvements in order to handle stopped containers
# (over time, containers need to be stopped after some time to avoid congestion)
#
# because it does not seem possible to change the port bindings of a stopped container
# we need to have a means to collect the port numbers already allocated to stopped containers
#
# we could ignore running containers but that would not change much
# in addition, the free_port() method remembers the allocated port,
# so in principle refresh_used_ports needs to be run only once at startup time
# although for safety it should/could/will be cached for an hour or something
#

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PortPool(metaclass=Singleton):

    def __init__(self):
        self.containers = None
        self.used_ports = set()

    def reset(self):
        self.containers = None
        
    # xxx need to cache this for a few minutes at least
    def get_containers(self):
        if self.containers is None:
            proxy = docker.from_env()
            self.containers = proxy.containers.list()
        return self.containers
    
    def refresh_used_ports(self):
        myset = set()
        self.get_containers()
        for container in self.containers:
            try:
                portbindings = container.attrs['HostConfig']['PortBindings']
                # looks like this
                # {'8888/tcp': [{'HostIp': '', 'HostPort': '47001'}]}
                for k, v in portbindings.items():
                    for d in v:
                        myset.add(int(d['HostPort']))
            except Exception as e:
                print("Something wring in PortPool", e)
                traceback.print_exc()
        self.used_ports = myset

    def free_port(self):
        self.refresh_used_ports()
        # xxx production code would need some watchdog here
        while True:
            port = self.stateless_free_port()
            if port not in self.used_ports:
                return port
            else:
                print("PortPool: rejecting allocated port {}".format(port))
            
    def record_as_used(self, port):
        self.used_ports.add(int(port))

    # http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python/2838309#2838309
    @staticmethod
    def stateless_free_port():
        "return a free TCP port"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("",0))
            # not required
            # s.listen(1)
            return s.getsockname()[1]

##############################
# used by the test-dockers load test script
# in that context port conflicts do not matter much
if __name__ == '__main__':
    import sys
    how_many = int(sys.argv[1])
    pool = PortPool()
    pool.refresh_used_ports()
    if how_many > 1:
        print("pool -> ", pool.used_ports)
        print("The ports returned by free_port when run {} times".format(how_many),
              file=sys.stderr)
    for i in range(how_many):
        print(pool.stateless_free_port())
    

