#!/bin/bash

# one-shot utility
# developped originally for the nbautoeval exercises of the MOOC on Python3
# point is that the exercise notebooks in questions were tagged 
# with nbformat being 4.1
# it turns out that as soon as the student runs the cells, they create
# ipywidget instances in the notebook and that creates painful 
# user experience (warnings each time the notebook autosaves...)
# hence this patch

function one-file() {
    local filename="$1"; shift

    sed -i.nbf -e 's/\("nbformat_minor":\) \([0-9]\)/\1 4/' "$filename"
}

for file in "$@"; do
    one-file "$file"
done
