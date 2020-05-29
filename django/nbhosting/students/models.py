from django.db import models

# Create your models here.

# a Student is currently implemented as a regular 
# django User instance
# so no need to change the ORM or to store anything in the DB

import podman
podman_url = "unix://localhost/run/podman/podman.sock"

class Student:
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return f'Student {self.name}'
        
    def spot_running_containers(self):
        """
        returns a list of containers that are currently
        running under this student's name
        
        """
        
        terminator = f"-x-{self.name}"
        
        with podman.ApiConnection(podman_url) as podman_api:
            # not specifying all=True means only the running ones
            containers = podman.containers.list_containers(podman_api)
        # keep only this student's containers
        # the drawback of using sparse=True however 
        # is that the container structures are not fully filled
        # hence this convoluted way of chking for their names
        containers = [
            container for container in containers 
            if container['Names'][0].endswith(terminator)
        ]
        return containers
        
        
    def kill_running_containers(self, *, containers=None, background=False):
        """
        kills containers passed as arguments
        
        typically containers should be the result of self.spot_running_containers()
        and this is what is being called if containers is not provided
        
        background says whether this call should return immedialtely (background=True)
        or wait until the containers are actually killed (background=False)

        """
        if containers is None:
            containers = self.spot_running_containers()
            
        with podman.ApiConnection(podman_url) as podman_api:
            for container in containers:
                podman.containers.kill(podman_api, container['Names'][0])

        
