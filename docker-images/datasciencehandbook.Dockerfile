# trying the big image
FROM jupyter/scipy-notebook:latest


####################
# for interfacing with nbhosting, we need this startup script in all images
# and we need to be root again for installing stuff
####################
USER root
COPY start-in-dir-as-uid.sh /usr/local/bin
