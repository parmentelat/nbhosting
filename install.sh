#!/bin/bash

# can do installs or updates
# expected to run in a repository that is git-updated
# run as ./install.sh

# where all the data lies; may provisions were made in the code to
# have this configurable (in the django settings)
# but there might still be other places where it's hard-wired
# so it's safer to use this for now
nbhroot=/nbhosting

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
    # expand frame_ancestors
    sed -e "s,@frame_ancestors@,$frame_ancestors," \
        jupyter/jupyter_notebook_config.py.in > jupyter/jupyter_notebook_config.py
    mkdir -p $root/jupyter
    rsync $rsopts jupyter/ $root/jupyter/
}

function update-uwsgi() {
    sed -e "s,@srcroot@,$srcroot," \
        -e "s,@nbhroot@,$nbhroot," uwsgi/nbhosting.ini.in > uwsgi/nbhosting.ini
    rsync $rsopts uwsgi/nbhosting.ini /etc/uwsgi.d/
}

function update-assets() {
    local assets_root=/var/nginx/nbhosting
    mkdir -p $assets_root
    rsync $rsopts nbhosting/assets/ $assets_root/assets/
    chown -R nginx:nginx $assets_root/snapshots
}

function update-images() {
    rsync $rsopts ./images $nbhroot/
}

function update-nginx() {

    # update both configs from the .in
    local configs="nginx-https.conf nginx-http.conf"
    local config
    for config in $configs; do
        sed -e "s,@nbhroot@,$nbhroot," \
            -e "s,@server_name@,$server_name,g" \
            -e "s,@ssl_certificate@,$ssl_certificate,g" \
            -e "s,@ssl_certificate_key@,$ssl_certificate_key,g" \
            nginx/$config.in > nginx/$config
    done

    if [ "$server_mode" != "http" ]; then
        config="nginx-https.conf"
    else
        config="nginx-http.conf"
    fi
    rsync $rsopts nginx/$config /etc/nginx/nginx.conf
}

function restart-services() {
    systemctl restart nbh-monitor
    systemctl restart nginx
    systemctl restart nbh-uwsgi
}

function enable-services() {
    # patch for f27
    if grep -q 'Fedora release 27' /etc/fedora-release; then
        rsync $rsopts systemd/nbh-uwsgi.service /etc/systemd/system/
    else
        rsync $rsopts systemd/nbh-uwsgi.service.f27 /etc/systemd/system/
    fi
    rsync $rsopts systemd/nbh-monitor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable docker
    systemctl enable nginx
    systemctl enable nbh-uwsgi
    systemctl enable nbh-monitor
}

function default-main() {
    check-subdirs
    ensure-uid-1000

    update-bins
    update-jupyter
    update-uwsgi
    update-assets
    update-images

    update-nginx
    enable-services
    restart-services

    # this is just convenience
    log-symlink
}

# with no argument we run default-main
# otherwise one can invoke one or several steps
# with e.g. install.sh update-uwsgi log-symlink
function main() {
    # sitesettings.py needs to be installed first,
    # so that sitesettings.sh reflect any change
    update-python-libraries

    # probe sitesettings.py
    nbhosting/manage.py list-siteconfig > nbhosting/main/sitesettings.sh
    source nbhosting/main/sitesettings.sh

    if [[ -z "$@" ]]; then
	default-main
    else
	for command in "$@"; do $command; done
    fi
}

main "$@"
