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

function swap-ip() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-production" ]; then
        systemctl stop nbhosting-dev-addr
        systemctl disable nbhosting-dev-addr
        systemctl start nbhosting-addr
        systemctl enable nbhosting-addr
    else
        systemctl stop nbhosting-addr
        systemctl disable nbhosting-addr
        systemctl start nbhosting-dev-addr
        systemctl enable nbhosting-dev-addr
    fi
}

##### (*) SSL
# nginx is configured to use a servername and related
# certificate file

function swap-ssl() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    cd /root/nbhosting/django/nbh_main

    if [ "$mode" == "become-production" ]; then
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate/bundle.crt",' \
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key",' \
            sitesettings.py
    else
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting-dev.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate-dev/bundle.crt",' \
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate-dev/nbhosting-dev.inria.fr.key",' \
            sitesettings.py
    fi

#    cd /root/nbhosting
#    ./install.sh
}

function -pull-from() {
    # in terms of contents, we should only worry about
    # /nbhosting/students
    # /nbhosting/raw
    #
    # also we pull in 2 dirs that are called
    # /nbhosting/students.prod
    # /nbhosting/raw.prod
    # so we can continue operate the dev site with minimal impact

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
    local current_host=$1; shift

    set -x
    rsync $rsync_opt -a --delete \
        $current_host:/root/nbhosting/db.sqlite3 /nbhosting/${mode}/
    set +x
    local contents="courses  courses-git  images  jupyter  local  logs	modules  raw  static  students"
    for content in $contents; do
        set -x
        rsync $rsync_opt -a --delete \
            $current_host:/nbhosting/${content}/ /nbhosting/${mode}/${content}/
        set +x
    done
}

function pull-from-prod() {
    -pull-from prod "$@"
}
function pull-from-dev() {
    -pull-from dev "$@"
}

###
### function orchestrate() {
###     local usage="Usage: $FUNCNAME current-official new-official
###  Example:
###   $FULLPATH thurst.inria.fr thermals.inria.fr
### "
###
###     current=$1; shift
###     new=$1; shift
###
###     # copy this script over in /tmp on both boxes
###     for h in $current $new; do
###         -echo-stderr "Pushing $FULLPATH onto $h in /tmp"
###         rsync -ai $FULLPATH root@$h:/tmp
###     done
###     ssh root@${current} /tmp/$COMMAND xxx etc...
###

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


# xxx from older version
# because the outcome of this script goes on stdout,
# so we always write on stderr, but as far as stderr is concerned,
# we want to log it *and* to return it in stderr
# xxx previous redirection system
# main 2> >(tee -a $log >&2) || :


call-subcommand "$@"
