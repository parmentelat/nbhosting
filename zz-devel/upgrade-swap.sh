#!/bin/bash
#
# we have 2 boxes thurst and thermals that play the roles
# of nbhosting and nbhosting-dev on the inria.fr domain
#
# in general we have
# thurst on nbhosting        - it's the big one - and
# thermals on nbhosting-dev  - a more modest setup, although quite decent
#
# the purpose of this script is to automate swapping these roles
#
# we need this initially so that we can upgrade thurst from f25 to f27
#
####################
#
# several things need to be taken care of
#
##### (*) IP
# the following DNS names are defined
#
# nbhosting.inria.fr     138.96.19.1
# thurst.inria.fr        138.96.19.2
# thermals.inria.fr      138.96.19.4
# nbhosting-dev.inria.fr 138.96.19.14
#
# we don't use DNS to swap because it is so slow to propagate
# instead, each box has systemd services defined to take or release
# the 2 addresses

FULLPATH=$0
COMMAND=$(basename $0)

function -echo-stderr() {
    >&2 echo $(date "+%H:%M:%S") "$@"
}

function -die() {
    -echo-stderr "$@"
    exit 1
}

#####

function -pull-from() {

    # this is granted
    local mode="$1"; shift

    local OPTIND
    local opt
    local rsync_opt=""
    while getopts "ni" opt; do
        case $opt in
            n) rsync_opt="$rsync_opt -n" ;;
            i) rsync_opt="$rsync_opt -i" ;;
            *) -die "USAGE: pull-from-${mode} [-n] hostname" ;;
        esac
    done

    shift $((OPTIND-1))

    [[ "$#" -eq 1 ]] || -die "USAGE: pull-from-${mode} [-n] hostname"
    local mode_host=$1; shift

    set -x
    rsync $rsync_opt -a --delete \
        $mode_host:/nbhosting/${mode}/ /nbhosting/${mode}/
}

function pull-from-prod() {
    -pull-from prod "$@"
}
function pull-from-dev() {
    -pull-from dev "$@"
}

#####

function swap-ip() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-prod" ]; then
        systemctl stop nbhosting-dev-addr
        systemctl disable nbhosting-dev-addr
        systemctl enable nbhosting-addr
        # don't do this yet
        echo DO LATER: systemctl start nbhosting-addr
    elif [ "$mode" == "become-dev" ]; then
        systemctl stop nbhosting-addr
        systemctl disable nbhosting-addr
        systemctl enable nbhosting-dev-addr
        echo DO LATER: systemctl start nbhosting-dev-addr
    else
        echo ignoring unknown mode $mode
    fi
}

##### (*) SSL
# nginx is configured to use a servername and related
# certificate file

function swap-ssl() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    cd /root/nbhosting/django/nbh_main

    if [ "$mode" == "become-prod" ]; then
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate/bundle.crt",' \
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key",' \
            sitesettings.py
    elif [ "$mode" == "become-dev" ]; then
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting-dev.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate-dev/bundle.crt",' \
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate-dev/nbhosting-dev.inria.fr.key",' \
            sitesettings.py
    else
        echo ignoring unknown mode $mode
    fi

}

function swap-contents() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-prod" ]; then
        cd /nbhosting
        rm current
        ln -s prod current
    elif [ "$mode" == "become-dev" ]; then
        cd /nbhosting
        rm current
        ln -s dev current
    else
        echo ignoring unknown mode $mode
    fi
}

# ignore unrelevant  nbh-autopull
SERVICES="nbhosting-addr nbhosting-dev-addr nbh-django nbh-monitor nginx docker"
CONFIG=$HOME/nbhosting/django/nbh_main/sitesettings.py

function status() {
    for service in $SERVICES; do
        echo ===== $service =====
        systemctl is-active $service
        systemctl is-enabled $service
    done
    echo '===== configuration ====='
    egrep '^(server_name|ssl_certificate)' $CONFIG
    echo '===== data space ====='
    ls -l /nbhosting/current
}


# very rough for now; run all stages individually and manually

function call-subcommand() {

    # first argument is a subcommand in this file
    local fun="$1"
    case $(type -t -- $fun) in
	function)
	    shift ;;
	*)  -die "$fun not a valid subcommand - use either swap-ip / swap-ssl / pull-from-prod / pull-from-dev" ;;
    esac
    # call subcommand
    $fun "$@"
}

call-subcommand "$@"
