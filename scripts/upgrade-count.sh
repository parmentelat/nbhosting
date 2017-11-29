#!/bin/bash

# this helper script scans a file created by upgrade-snapshot.sh
# and counts the number of containers per image
#
# without argument all the files that look like a snapshot
# are taken into account
#
# TMP: for now the image hashes are hard-coded, something
# smarter will be needed mid-term

files="$@"

[ -z "$files" ] && files="??-??-??-??*"

old=b60eeec
new=8a44ed6

for file in $files; do
    echo ==================== $file
    echo -n "old "; grep $old $file | wc -l 
    echo -n "new "; grep $new $file | wc -l
done
