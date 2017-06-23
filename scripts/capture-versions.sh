#!/bin/bash

set -x

rpm -aq | grep '^python3'

pip3 list

python3 --version

python3 -c 'import django; print(django.__version__)'
