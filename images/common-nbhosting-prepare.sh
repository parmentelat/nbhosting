#!/bin/bash

set -x

# --------
# update base updaters

apt-get update

pip install -U pip setuptools

# --------
# this is to increase the ulimit -n (max nb of open files)
# as perceived by regular user processes in the container
# before we implement this setting, default was 1024
# 128 * 1024 looks about right
# container root was OK at 1024*1024
for type in hard soft; do echo '*' $type nofile 131072 ; done > /etc/security/limits.d/open-file.conf


# add lsof in the mix to help troubleshoot shortages of open files
# from the container context
apt-get install lsof


# --------
# hacks for jupyter itself
# (*) disable check done when saving files - see https://github.com/jupyter/notebook/issues/484
# (*) disable the 'Trusted' notification widget
# (#) remove the 'Notebook saved' message that annoyingly pops up
find /opt /usr -name notebook.js -o -name main.min.js | \
    xargs sed -i \
        -e 's|if (check_last_modified)|if (false)|'


find /opt /usr -name notificationarea.js -o -name main.min.js | \
    xargs sed -i \
        -e 's|this.init_trusted_notebook_notification_widget();||' \
        -e 's|nnw.set_message(i18n.msg._("Notebook saved"),2000);||' 


# --------
# git from inside

# configure git
sudo -u jovyan git config --global user.email "notebook.user@example.org" 
sudo -u jovyan git config --global user.name "Notebook User"

# jupyterlab git extension
jupyter labextension install @jupyterlab/git && pip install --upgrade jupyterlab-git && jupyter serverextension enable --py jupyterlab_git

# the nbgitpuller thingy - turned off
# pip install git+https://github.com/parmentelat/nbgitpuller@nbhmaster && jupyter serverextension enable --py nbgitpuller

# --------
# useful additions and extensions

# install jupyter extensions
pip install ipywidgets && jupyter nbextension enable --py widgetsnbextension

# install contrib extensions including splitcell
pip install jupyter_contrib_nbextensions && jupyter contrib nbextension install --system
# enable splitcell nbextension
jupyter nbextension enable splitcell/splitcell

# auto-evaluated exercices
pip install nbautoeval

# the ipythontutor magic
pip install ipythontutor

# beg. Sep. 2019
# when building an ijavascript kernel 
# I ran into /home/jovyan/.npm being owned by root at this point
# which broke npm builds
# it probably means that we should run one of the steps above
# as jovyan instead of root, but as a quick and dirty workaround:
chown -R jovyan:users /home/jovyan/.npm
