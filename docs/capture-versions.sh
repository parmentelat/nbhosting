#!/bin/bash

set -x

##### core pieces
rpm -q docker nginx uwsgi

##### python3 core pieces
python3 --version
python3 -c 'import django; print(django.__version__)'

##### python libraries installed with dnf
rpm -aq | grep '^python3'

##### python libraries installed with pip
pip3 freeze
