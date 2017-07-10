# --------
# using scipy, it's kinda big but that should not be a problem
# base-notebook lacks at least numpy, widgets, so...
# xxx we should specify a fixed version probably though
FROM jupyter/scipy-notebook:latest


# --------
# for interfacing with nbhosting, we need this startup script in all images
# and we need to be root again for installing stuff
USER root
COPY start-in-dir-as-uid.sh /usr/local/bin


# --------
# how to install additional packages to the underlying python
# assuming that all the bioinfo notebooks will move to python3
RUN conda install -y mpld3


# --------
# hacks for jupyter itself
# (*) disable check done when saving files - see https://github.com/jupyter/notebook/issues/484
# (*) disable the 'Trusted' notification widget
RUN (find /opt /usr -name notebook.js -o -name main.min.js | xargs sed -i -e 's|if (check_last_modified)|if (false)|') \
 &&  (find /opt /usr -name notificationarea.js -o -name main.min.js | xargs sed -i -e 's|this.init_trusted_notebook_notification_widget();||')

