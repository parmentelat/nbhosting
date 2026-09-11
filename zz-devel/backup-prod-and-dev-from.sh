#!/bin/bash

sources="/nbhosting/prod /nbhosting/dev"

function local_backup() {
    for source in $sources; do
        local dest=$source.$(hostname -s)
        echo "$(date) - backing up $source to $dest"
        rsync -a --delete $source/ $dest/
    done
}

function remote_backup() {
    local hostname=$1; shift
    for source in $sources; do
        local remote=$(cut -d. -f1 <<< $hostname)
        local dest=$source.$remote
        echo "$(date) - backing up $hostname:$source to $dest"
        rsync -a --delete $hostname:$source/ $dest
    done
}

hostname="$1"; shift

if [ -n "$hostname" ]; then
    remote_backup $hostname
else
    local_backup
fi
