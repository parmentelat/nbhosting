#!/bin/bash

# globals that can be changed through options
DEVEL_MODE=

# can do installs or updates
# expected to run in a repository that is git-updated
# run as ./install.sh 

# essentially: here
srcroot=$(pwd -P)

# where all the data lies; may provisions were made in the code to
# have this configurable (in the django settings)
# but there might still be other places where it's hard-wired
# so it's safer to use this for now
root=/nbhosting

function check-subdirs() {
    for subdir in jupyter courses-git logs raw; do
	[ -d $root/$subdir ] || mkdir -p $root/$subdir
    done
}

# not quite crucial, but safer
# we make sure that uid 1000 is used, so that none of the
# dynamically created users takes that id
# this way we avoid confusion since jovyan has uid 1000 in the jupyter images
function ensure-uid-1000() {
    id 1000 >& /dev/null || {
	useradd nbhjovyan --uid 1000 --home /home/nbhjovyan
    }
}

# rsync options
rsopts=-rltpv

# create the /var/log/nbhosting symlink
function log-symlink() {
    local varlink=/var/log/nbhosting
    [ -h $varlink ] || ln -sf $root/logs $varlink
}

function update-python-libraries() {
    ./setup.py install
}

function update-bins() {
    rsync $rsopts scripts/nbh* /usr/bin
}

function update-jupyter() {
    mkdir -p $root/jupyter
    rsync $rsopts jupyter/ $root/jupyter/
}

function update-uwsgi() {
    sed -e "s,@DJANGO-ROOT@,$srcroot/nbhosting," uwsgi/nbhosting.ini.in > uwsgi/nbhosting.ini
    rsync $rsopts  uwsgi/nbhosting.ini /etc/uwsgi.d/
}

function update-assets() {
    local root=/var/nginx/nbhosting
    mkdir -p $root
    rsync $rsopts nbhosting/assets/ $root/assets/
    chown -R nginx:nginx $root
}

function update-nginx() {
    local config
    if [ -z "$DEVEL_MODE" ] ; then
        config="nginx-https.conf"
    else
        config="nginx-http.conf"
    fi
    rsync $rsopts nginx/$config /etc/nginx/nginx.conf
    # xxx remove sequels
    rm -f /etc/nginx/conf.d/nbhosting.conf
}
    
function restart-services() {
    systemctl restart nginx
    systemctl restart nbh-uwsgi
    systemctl restart nbh-monitor
}

function enable-services() {
    rsync $rsopts systemd/nbh-uwsgi.service /etc/systemd/system/
    rsync $rsopts systemd/nbh-monitor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable docker
    systemctl enable nginx
    systemctl enable nbh-uwsgi
    systemctl enable nbh-monitor
}

function turn-on-debug-if-develop() {
    [ -z "$DEVEL_MODE" ] && return
    (cd nbhosting/main; sed -i.git -e "s,^DEBUG.*,DEBUG = True," settings.py)
}

function default-main() {
    check-subdirs
    ensure-uid-1000

    update-python-libraries
    update-bins
    update-jupyter
    update-uwsgi
    update-assets
    
    update-nginx
    enable-services
    restart-services

    turn-on-debug-if-develop

    # this is just convenience
    log-symlink
}

# with no argument we run default-main
# otherwise one can invoke one or several steps
# with e.g. install.sh update-uwsgi log-symlink
function main() {
    # d stands for development
    while getopts "d" opt; do
        case $opt in
            d) DEVEL_MODE=true;;
            \?) echo "unknown option $opt - exiting"; exit 1;;
        esac
    done
    shift $(($OPTIND - 1))
    
    if [[ -z "$@" ]]; then
	default-main
    else
	for command in "$@"; do $command; done
    fi
}

main "$@"
