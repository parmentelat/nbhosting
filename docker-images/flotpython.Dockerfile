# xxx would make sense to use some fix version some day
FROM jupyter/scipy-notebook:latest

####################
# for interfacing with nbhosting, we need these 2 things in all images
# and we need to be root again for installing stuff
####################
USER root
RUN apt-get update && apt-get install sudo
COPY start-in-dir-as-uid.sh /usr/local/bin

####################
# appearance and behaviour of jupyter itself
####################
# (1) disable these widgets as otherwise they cause the 'Widgets' submenu in the menubar
# to appear again even though we turn it off in custom.js
# this is not desirable of course on the longer term
# Sylvain Corlay said he would help in fixing this someday
RUN jupyter nbextension disable jupyter-js-widgets/extension

# (2) disable check done when saving files
# see https://github.com/jupyter/notebook/issues/484
RUN find /opt /usr -name notebook.js | grep static/notebook/js/notebook.js | xargs sed -i -e 's,if (check_last_modified),if (false),'
