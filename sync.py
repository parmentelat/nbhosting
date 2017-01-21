#!/usr/bin/env python3

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, Push, ColonFormatter

paths_str = "edxfront manage.py nbhosting scripts ports"

verbose = False

nbhosting = SshNode(
    hostname="nbhosting.inria.fr",
    username="root",
    formatter=ColonFormatter(verbose=True),
)

def sync():
    s = Scheduler()

    SshJob(node=nbhosting,
           scheduler=s,
           verbose=verbose,
           keep_connection=True,
           commands=[
               Push(localpaths=paths_str.split(), remotepath="nbhosting-sync/",
                    recurse=True, preserve=True),
               Push(localpaths="public_html", remotepath="/var/lib/nginx/",
                    recurse=True),
           ])
               
    SshJob(node=nbhosting,
           scheduler=s,
           verbose=verbose,
           keep_connection=True,
           commands=[
               Push(localpaths="nginx/nbhosting.conf", remotepath="/etc/nginx/conf.d"),
               Run("systemctl restart nginx"),
               ])
               
    SshJob(node=nbhosting,
           scheduler=s,
           verbose=verbose,
           keep_connection=True,
           commands=[
               Push(localpaths="uwsgi/nbhosting.ini", remotepath="/etc/uwsgi.d/"),
               Push(localpaths="uwsgi/nbhosting.service", remotepath="/etc/systemd/system/"),
               Run("systemctl daemon-reload"),
               Run("systemctl restart nbhosting"),

           ])

    s.orchestrate() or s.debrief()

def forever():
    while True:
        sync()
        input("Again ? ")

forever()
    
               
    
