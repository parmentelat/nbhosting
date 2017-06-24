# trying the big image
FROM jupyter/scipy-notebook:latest

####################
# for interfacing with nbhosting, we need these 2 things in all images
# and we need to be root again for installing stuff
####################
USER root
RUN apt-get update && apt-get install sudo
COPY start-in-dir-as-uid.sh /usr/local/bin

# leaving this out for now, so we can have a reference point
# of the outcome of leaving things as-is
# disable these widgets as otherwise they cause the 'Widgets' submenu in the menubar
# to appear again even though we turn it off in custom.js
# RUN jupyter nbextension disable jupyter-js-widgets/extension
