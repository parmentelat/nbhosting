#!/bin/bash

# this helper script will create a snapshot file that shows
# container names together with their image hash
#
# it is useful for monitoring the deployment of a new image
#
# run with -a or --all to also scan containers that are asleep
# (just like docker ps)

ALL=""

case "$1" in
    -a|--all) ALL=true ;;
esac

###
if [ -n "$ALL" ] ; then
    ps_option="--all"
    file_ext=".all"
fi

date=$(date +%m-%d-%H-%M)
result=${date}${file_ext}

containers=$(docker ps $ps_option --format "{{.Names}}")
for c in $containers; do
    docker inspect --format "{{.Name}} -> {{.Image}}" $c
done > $result

echo result in $result 
