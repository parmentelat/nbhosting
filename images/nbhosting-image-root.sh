#!/bin/bash

set -x

# --------
# update base updaters

apt-get update; apt-get clean

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
apt-get install -y lsof

# needed to export build results
apt-get install -y rsync


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
# see also nbhosting-image-jovyan.sh for stuff run as jovyan
# --------
