#!/bin/bash
#
# installs etc-sysconfig-docker.<variant> into /etc/sysconfig/docker
#
# this is not done as part of the toplevel install.sh because
# (*) for now we want to try out several variants
# (*) restarting docker is very intrusive
#     - although we do this only when needed
#
# xxx NOTE xxx
# it would maybe have been more effective to use a daemon.json
# file to configure only these 2 settings
# like in https://sandro-keil.de/blog/2017/01/23/docker-daemon-tuning-and-json-file-configuration/ 

COMMAND=$(basename $0)
DIRNAME=$(dirname $COMMAND)

cd $DIRNAME

system_config="/etc/sysconfig/docker"

function die() {
    echo "$@"
    exit 1
}

function warning() {
    echo "WARNING - running this can and will trash your docker setup entirely"
    echo "so data loss is to be expected if you proceed"
    echo "Type Control-C to abort"; read _
}

function apply() {
    variant=$1; shift
    config=etc-sysconfig-docker.$variant
    [ -f $config ] || die "$config not found"
    cmp $config $system_config && {
	echo "No change in $system_config as compared with $config"
    } || {
	echo "Installing $config as $system_config"
	cp $config $system_config
	echo "Restarting docker"
	systemctl restart docker
    }
}

function main() {
    variant=$1
    warning
    apply $variant
}

main "$@"

    
