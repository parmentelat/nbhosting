#!/bin/bash

set -x

# we've seen at some point file /home/jovyan/.npm owned by root
# so, run as many things as possible as jovyan
# to minimize the risk to create leftovers owned by root

### git from inside the container

# configure git
git config user.email || git config --global user.email "default.user@nbhosting.io" 
git config user.name  || git config --global user.name "Nbhosting User"

# the nbgitpuller thingy - turned off
# pip install git+https://github.com/parmentelat/nbgitpuller@nbhmaster && jupyter serverextension enable --py nbgitpuller

# --------
# useful additions and extensions

# install jupyter extensions
pip install ipywidgets && jupyter nbextension enable --py widgetsnbextension

# install contrib extensions including splitcell
pip install jupyter_contrib_nbextensions && jupyter contrib nbextension install --user
# enable splitcell nbextension
jupyter nbextension enable splitcell/splitcell

# we may use jupytext in the future for smoother git pull from the students space
pip install jupytext

# auto-evaluated exercices
pip install nbautoeval

# the ipythontutor magic
pip install ipythontutor

# jupyterlab git extension
jupyter labextension install @jupyterlab/git && pip install --upgrade jupyterlab-git && jupyter serverextension enable --py jupyterlab_git