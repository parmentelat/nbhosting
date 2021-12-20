#!/bin/bash

set -x

cat /etc/fedora-release

uname -a

##### core pieces
rpm -q podman nginx redis

##### python3 core pieces
python3 --version
python3 -c 'import django; print(f"{django.__version__=}")'
python3 -c 'import gunicorn; print(f"{gunicorn.__version__=}")'

##### python libraries installed with dnf
rpm -aq | grep '^python3'

##### python libraries installed with pip
pip3 freeze
