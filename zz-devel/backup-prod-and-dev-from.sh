#!/bin/bash

sources="/nbhosting/prod /nbhosting/dev"

function local_backup() {
    for source in $sources; do
        local dest=$source.$(hostname -s)
        echo "$(date) - backing up $source to $dest"
        rsync -a --delete $rsync_opts $source/ $dest/
    done
}

function remote_backup() {
    local hostname=$1; shift
    for source in $sources; do
        local remote=$(cut -d. -f1 <<< $hostname)
        local dest=$source.$remote
        echo "$(date) - backing up $hostname:$source to $dest"
        rsync -a --delete $rsync_opts $hostname:$source/ $dest
    done
}

function usage() {
    echo "Usage: $(basename $0) [-i] [-n] [hostname]"
    echo "  -i    pass -i (itemize-changes) to rsync"
    echo "  -n    pass -n (dry-run) to rsync"
    exit 1
}

rsync_opts=""
while getopts "in" opt; do
    case $opt in
        i) rsync_opts="$rsync_opts -i" ;;
        n) rsync_opts="$rsync_opts -n" ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

hostname="$1"; shift

if [ -n "$hostname" ]; then
    remote_backup $hostname
else
    local_backup
fi
