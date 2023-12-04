#!/bin/bash

set -x

# 2023 Dec: moving to using jupyterlab4 / nb7
# see .nbhosting/Dockerfile in flotpython/course
# for instructions on how to adapt your Dockerfile
# if moving over from nbclassic


# we've seen at some point file /home/jovyan/.npm owned by root
# so, run as many things as possible as jovyan
# to minimize the risk to create leftovers owned by root

### git from inside the container

# configure git
git config user.email || git config --global user.email "default.user@nbhosting.io"
git config user.name  || git config --global user.name "Nbhosting User"
# as of summer 2022, this seems to become needed
# for smoother operation of jupyterlab-git
git config --global --add safe.directory '*'
# for use from a jlab terminal
git config --global alias.l 'log --oneline --graph'
git config --global alias.la 'log --oneline --graph --all'
git config --global alias.s 'status'

# jupyterlab
pip install -U jupyter
# and its git extension (no post-install required since jupyterlab-v3)
# looks like it's broken within jlab4 ?
pip install -U jupyterlab-git

# we heavily use jupytext so we can get along with git
pip install -U jupytext
