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

    cd /root/nbhosting/nbhosting/main
    
    if [ "$mode" == "become-production" ]; then
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate/bundle.crt",'
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key",' \
            sitesettings.py
    else
        sed -i.swapped \
            -e 's,^server_name *=.*,server_name = "nbhosting-dev.inria.fr",' \
            -e 's,^ssl_certificate *=.*,ssl_certificate = "/root/ssl-certificate-dev/bundle.crt",'
            -e 's,^ssl_certificate_key *=.*,ssl_certificate_key = "/root/ssl-certificate-dev/nbhosting-dev.inria.fr.key",' \
            sitesettings.py
    fi

    cd /root/nbhosting
    ./install.sh
}

function pull-students() {
    # in terms of contents, we should only worry about
    # /nbhosting/students

    mode=$1; shift
    previous_official=$1; shift

    [ -n "$previous_official" ] || -die "$FUNCNAME bad arg nb"

    if [ "$mode" == "become-production" ]; then
        echo "Pulling /nbhosting/students from $previous_official"
        cd /nbhosting
        rsync "$@" -a --delete $previous_official:/nbhosting/students/ /nbhosting/students/
    else
        echo "first arg is mode and must be become-production"
    fi
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
	*)  -die "$fun not a valid subcommand - use either swap-ip / swap-ssl / pull-students" ;;
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
