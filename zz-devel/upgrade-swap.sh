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
# the 2 addresses:
# nbhosting-addr.service
# nbhosting-dev-addr.service

FULLPATH=$0
COMMAND=$(basename $0)

function -echo-stderr() {
    >&2 echo -e $(date "+%H:%M:%S") "$@"
}

function -die() {
    -echo-stderr "$@"
    exit 1
}

#####
function -sanity-check() {
    local function=$1; shift
    local service=$1; shift
    echo -n "checking for service $service to be active .. "
    if ! systemctl is-active $service >& /dev/null ; then
        echo KO
        echo "WARNING: $function should be run from a node that has $service active"
        echo "this does not seem to be the case..."
        echo -n "type 'yes' to proceed : "
        read answer
        [ "$answer" == "yes" ] || { echo "bye ..." ; exit 1; }
    else
        echo OK
    fi

}


function disk-status() {
    du -hs /nbhosting/{dev,prod}*
}


function -pull-from() {

    # this is mandatory
    local mode="$1"; shift
    local access="$1"; shift

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
    local fqdn_host=$1; shift
    local simple_host=$(cut -d. -f1 <<< ${fqdn_host})

    case "$mode" in
      prod|dev) ;;
      *) -die "wrong mode $mode" ;;
    esac

    case "$access" in
      local) from_url="/nbhosting/${mode}.${simple_host}/" ;;
      remote) from_url="$fqdn_host:/nbhosting/${mode}/" ;;
      *) -die "wrong access $access" ;;
    esac

    set -x
    rsync $rsync_opt -a --delete \
        $from_url /nbhosting/${mode}/
}

function fasttrack-from-prod() {
    -sanity-check pull-from-prod nbhosting-dev-addr
    -pull-from prod local "$@"
}
function fasttrack-from-dev() {
    -sanity-check pull-from-dev nbhosting-addr
    -pull-from dev local "$@"
}
function pull-from-prod() {
    -sanity-check pull-from-prod nbhosting-dev-addr
    -pull-from prod remote "$@"
}
function pull-from-dev() {
    -sanity-check pull-from-dev nbhosting-addr
    -pull-from dev remote "$@"
}

#####

function swap-ip-down() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-prod" ]; then
        systemctl stop nbhosting-dev-addr
        systemctl disable nbhosting-dev-addr
    elif [ "$mode" == "become-dev" ]; then
        systemctl stop nbhosting-addr
        systemctl disable nbhosting-addr
    else
        echo ignoring unknown mode $mode
    fi
}

function swap-ip-up() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-prod" ]; then
        systemctl enable nbhosting-addr
        systemctl start nbhosting-addr
    elif [ "$mode" == "become-dev" ]; then
        systemctl enable nbhosting-dev-addr
        systemctl start nbhosting-dev-addr
    else
        echo ignoring unknown mode $mode
    fi
}

##### (*) SSL
# nginx is configured to use a servername and related
# certificate file

function swap-sitesettings() {
    mode=$1; shift

    [ -n "$mode" ] || -die "$FUNCNAME bad arg nb"

#    cd /root/nbhosting/django/nbh_main
    cd /root

    if [ "$mode" == "become-prod" ]; then
        sed -i.swapped \
            -e 's,^production_box *=.*,production_box = True,' \
            sitesettings.py
    elif [ "$mode" == "become-dev" ]; then
        sed -i.swapped \
            -e 's,^production_box *=.*,production_box = False,' \
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

function nginx-down() {
    sed -i -e 's/set $down 0;/set $down 1;/' /etc/nginx/nginx.conf
    systemctl restart nginx
}

# ignore unrelevant  nbh-autopull
SERVICES="nbhosting-addr nbhosting-dev-addr nbh-django nbh-monitor nginx"
CONFIG=$HOME/nbhosting/django/nbh_main/sitesettings.py

function status() {
    for service in $SERVICES; do
        echo ===== $service =====
        systemctl is-active $service
        systemctl is-enabled $service
    done
    echo '===== sitesettings configuration ====='
    grep -E '^(production_box)' $CONFIG
    echo '===== data space ====='
    ls -l /nbhosting/current
}

USAGE="not a valid subcommand - use either
  * status
  * disk-status
  * fasttrack-from-prod / fasttrack-from-dev
  * pull-from-prod / pull-from-dev
  * swap-ip-down / swap-sitesettings / swap-contents / swap-ip-up
  * nginx-down
"

HELP="
a few more words

* fasttrack-from-prod otherbox.inria.fr (or from-dev)
  in order to make the first sync
  it takes advantage of the prod.otherhost folder that is a (nightly crontab) local mirror
  i.e. this will sync e.g. /nbhosting/prod.otherbox into /nbhosting/prod
  which will be much faster than using pull, which does the same but over the network

* nginx-down
  set the 'down' flag to 1 in the nginx conf, and restart nginx that way
  nginx will then unconditionnally display a 'under maintenance' page
  this change will be undone by the next install.sh

  NOTE: makes sense to also stop the nbh-django service,
  and to make sure all containers are stopped
  (use the monitor with a small idle time)

* swap-ip-down become-prod (or become-dev)
  the current box will cease to bind the IP address for dev (resp. prod)

* pull-from-prod otherbox.inria.fr (or from-dev)
  in order to really sync the other box's prod tree locally
  do this once the service has been turned down

* swap-sitesettings become-prod (or become-dev)

* swap-contents become-prod (or become-dev)
  only change the current/ symlink in /nbhosting

* swap-ip-up become-prod (or become-dev)
  the current box will bind the IP address for prod (resp. dev)

do not forget to re-run install.sh once everything is done
so that nginx is enabled again

"


# very rough for now; run all stages individually and manually

function call-subcommand() {

    # first argument is a subcommand in this file
    local fun="$1"
    case $(type -t -- $fun) in
	function)
	    shift ;;
	*)  -die "$fun $USAGE" "$HELP" ;;
    esac
    # call subcommand
    $fun "$@"
}

call-subcommand "$@"
