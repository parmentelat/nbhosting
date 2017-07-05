# scipy is really big, but that should not be a problem
# xxx we should specify a fixed version probably though
FROM jupyter/scipy-notebook:latest
# an earlier attempt was using this smaller image instead
# but this lacks at least numpy, widgets, so...
#FROM jupyter/base-notebook:latest


####################
# for interfacing with nbhosting, we need this startup script in all images
# and we need to be root again for installing stuff
####################
USER root
COPY start-in-dir-as-uid.sh /usr/local/bin


####################
# hack for jupyter itself
####################
# (*) disable check done when saving files
# see https://github.com/jupyter/notebook/issues/484
RUN find /opt /usr -name notebook.js | grep static/notebook/js/notebook.js | xargs sed -i -e 's,if (check_last_modified),if (false),'
