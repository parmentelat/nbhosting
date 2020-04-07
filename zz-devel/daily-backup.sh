#!/bin/bash
sources="/nbhosting/prod /nbhosting/dev"
for source in $sources; do
    dest=$source.$(hostname -s)
    rsync -a $source/ $dest/
done
