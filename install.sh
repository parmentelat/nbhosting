#!/bin/bash

# can do installs or updates
# expected to run in a repository that is git-updated
# run as ./install.sh

# global config, like nbhroot and similar settings
# all come from django/nbh_main/sitesettings.py

function check-subdirs() {
    for subdir in jupyter courses-git logs raw local; do
        [ -d $nbhroot/$subdir ] || mkdir -p $nbhroot/$subdir
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
    [ -h $varlink ] || ln -sf $nbhroot/logs $varlink
}

function check-sitesettings() {
    local sitesettings="django/nbh_main/sitesettings.py"
    if [ ! -f $sitesettings ]; then
        echo "You need to write you site settings file $sitesettings"
        exit 1
    fi
}

function update-python-libraries() {
    # find_packages() requires to run in the right dir
    pip install django
}

function update-bins() {
    rsync $rsopts django/manage.py /usr/bin/nbh-manage
    rsync $rsopts scripts/nbh /usr/bin
    rsync $rsopts scripts/nbh-pull-student /usr/bin
}

function update-jupyter() {
    # expand frame_ancestors
    # need to go through a file script; sigh
    echo "s|@frame_ancestors@|${frame_ancestors[@]}|" > jupyter/ancestors.sed
    sed -f jupyter/ancestors.sed \
        jupyter/jupyter_notebook_config.py.in > jupyter/jupyter_notebook_config.py
    mkdir -p $nbhroot/jupyter
    rsync $rsopts jupyter/ $nbhroot/jupyter/
}

function update-uwsgi() {
    sed -e "s,@srcroot@,$srcroot," \
        -e "s,@nbhroot@,$nbhroot," uwsgi/nbhosting.ini.in > uwsgi/nbhosting.ini
    rsync $rsopts uwsgi/nbhosting.ini /etc/uwsgi.d/
}

function update-assets() {
    local static_root=/var/nginx/nbhosting
    mkdir -p $static_root
    rsync $rsopts django/assets/ $static_root/assets/
    mkdir -p $static_root/snapshots
    chown -R nginx:nginx $static_root/snapshots

    (cd django; manage.py collectstatic --noinput)
}

function update-images() {
    rsync $rsopts ./images $nbhroot/
}

function update-nginx() {

    # update config from the .in
    local config="nginx-https.conf"
    sed -e "s,@nbhroot@,$nbhroot," \
        -e "s,@server_name@,$server_name,g" \
        -e "s,@ssl_certificate@,$ssl_certificate,g" \
        -e "s,@ssl_certificate_key@,$ssl_certificate_key,g" \
        nginx/$config.in > nginx/$config

    [ "$server_mode" == "https" ] || {
        echo "****"
        echo "Since 0.18.0 only https is supported for server_mode"
        echo "nbhosting NOT INSTALLED PROPERLY"
        echo "****"
        exit 1
    }
        
    rsync $rsopts nginx/nginx-https.conf /etc/nginx/nginx.conf

}

function update-docker {
    sed -e "s,@dockerroot@,$dockerroot," \
    docker/daemon.json.in > /etc/docker/daemon.json
}

# old name was nbh-uwsgi - see issue #103
function remove-uwsgi-service() {
    # if that service is not known, we're good
    systemctl cat nbh-uwsgi >& /dev/null || return
    systemctl stop nbh-uwsgi
    systemctl disable nbh-uwsgi
    rm -f /etc/systemd/system/nbh-uwsgi.service
}

function enable-services() {
    remove-uwsgi-service
    rsync $rsopts systemd/nbh-django.service /etc/systemd/system/
    rsync $rsopts systemd/nbh-autopull.service /etc/systemd/system/
    rsync $rsopts systemd/nbh-autopull.timer /etc/systemd/system/
    sed -e "s,@monitor_period@,$monitor_period," \
        -e "s,@monitor_idle@,$monitor_idle," \
        systemd/nbh-monitor.service.in > /etc/systemd/system/nbh-monitor.service
    systemctl daemon-reload
    systemctl enable docker
    systemctl enable nginx
    systemctl enable nbh-django
    systemctl enable nbh-monitor
    systemctl enable nbh-autopull.timer
}

function migrate-database() {
# not quite sure why, but it seems safer to use manage.py here
    (cd django; manage.py migrate)
}

function restart-services() {
    systemctl restart nbh-monitor
    systemctl restart nginx
    systemctl restart nbh-django
    systemctl restart nbh-autopull.timer
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
    update-docker
    enable-services
    migrate-database
    restart-services

    # this is just convenience
    log-symlink
}

# with no argument we run default-main
# otherwise one can invoke one or several steps
# with e.g. install.sh update-uwsgi log-symlink
function main() {
    # the very first time we need sitesettings.py to exist
    check-sitesettings
    # sitesettings.py needs to be installed first,
    # so that sitesettings.sh reflect any change
    update-python-libraries

    # probe sitesettings.py
    django/manage.py shell_sitesettings > django/nbh_main/sitesettings.sh
    source django/nbh_main/sitesettings.sh

    if [[ -z "$@" ]]; then
        default-main
    else
        for command in "$@"; do $command; done
    fi

}

main "$@"
