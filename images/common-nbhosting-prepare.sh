#!/bin/bash

# --------
# update base updaters

apt-get update

pip install -U pip

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
# useful additions and extensions

# install jupyter extensions, none enabled though
pip install jupyter_contrib_nbextensions && jupyter contrib nbextension install --system

# auto-evaluated exercices
pip install nbautoeval

# the ipythontutor magic
pip install ipythontutor

# the nbgitpuller thingy
pip install git+https://github.com/parmentelat/nbgitpuller@nbhosting && jupyter serverextension enable --py nbgitpuller

# --------
# during a transition perdio we had to do this 
# but it is no longer necessary
# pip install tornado==4.5.3
