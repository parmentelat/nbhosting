from django.db import models

# Create your models here.

# a Student is currently implemented as a regular 
# django User instance
# so no need to change the ORM or to store anything in the DB

import docker

class Student:
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return f'Student {self.name}'
        
    def spot_running_containers(self):
        """
        returns a list of docker containers that are currently
        running under this student's name
        
        note: this list is obtained from 
        https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.list
        with sparse=True, so resulting containers only contain partial information
        """
        
        terminator = f"-x-{self.name}"
        
        proxy = docker.from_env(version='auto')
        # not specifying all=True means only the running ones
        containers = containers = proxy.containers.list(sparse=True)
        # keep only this student's containers
        # the drawback of using sparse=True however 
        # is that the container structures are not fully filled
        # hence this convoulted way of chking for their names
        containers = [
            container for container in containers 
            if container.attrs['Names'][0].endswith(terminator)
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
            
        for container in containers:
            container.kill()                

        
