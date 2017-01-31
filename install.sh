#!/bin/bash

# can do installs or updates
# expected to run in a repository that is git-updated
# run as ./install.sh 

# essentially: here
srcroot=$(pwd -P)

# where all the data lies; may provisions were made in the code to
# have this configurable (in the django settings)
# but there are still other places where it's hard-wired
# so it's safer to use this for now
root=/nbhosting

function check-subdirs() {
    for subdir in jupyter courses-git logs; do
	[ -d $root/$subdir ] || mkdir -p $root/$subdir
    done
}

# rsync options
rsopts=-rltpv

# create the /var/log/nbhosting symlink
function log-symlink() {
    local varlink=/var/log/nbhosting
    [ -h $varlink ] || ln -sf $root/logs $varlink
}

function update-uwsgi() {
    sed -e "s,@DJANGO-ROOT@,$srcroot/django," uwsgi/nbhosting.ini.in > uwsgi/nbhosting.ini
    rsync $rsopts  uwsgi/nbhosting.ini /etc/uwsgi.d/
    rsync $rsopts uwsgi/nbhosting.service /etc/systemd/system/
    systemctl restart nbhosting
}

function update-nginx() {
    rsync $rsopts nginx/nbhosting.conf /etc/nginx/conf.d/nbhosting.conf
    systemctl restart nginx
}
    
function update-bins() {
    rsync $rsopts scripts/nbh-* /usr/bin
}

function update-jupyter() {
    mkdir -p $root/jupyter
    rsync $rsopts jupyter/ $root/jupyter/
}

function main() {
    check-subdirs
    update-bins
    update-jupyter
    update-uwsgi
    update-nginx
    # this is just convenience
    log-symlink
}

main
