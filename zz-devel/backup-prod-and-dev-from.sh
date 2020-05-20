#!/bin/bash

sources="/nbhosting/prod /nbhosting/dev"

function local_backup() {
    for source in $sources; do
        local dest=$source.$(hostname -s)
        rsync -a --delete $source/ $dest/
    done
}

function remote_backup() {
    local hostname=$1; shift
    for source in $sources; do
        local remote=$(cut -d. -f1 <<< $hostname)
        local dest=$source.$remote
        rsync -a --delete $hostname:$source/ $dest
    done
}

hostname="$1"; shift

if [ -z "$hostname" ]; then
    local_backup
else
    remote_backup $hostname
fi
