# --------
# using scipy, it's kinda big but that should not be a problem
# base-notebook lacks at least numpy, widgets, so...
# FROM jupyter/scipy-notebook:latest
# we want to specify a fixed version
# in particular in oct. 2017 when using latest we had header-container
# still active when the notebooks showed up
FROM jupyter/scipy-notebook@sha256:d6ebaf357aa9cbc20aa8982b1860a454b90aa599377999212e2889ab5f764aea

# --------
# for interfacing with nbhosting, we need this startup script in all images
# and we need to be root again for installing stuff
USER root
COPY start-in-dir-as-uid.sh /usr/local/bin


# --------
# hacks for jupyter itself
# (*) disable check done when saving files - see https://github.com/jupyter/notebook/issues/484
# (*) disable the 'Trusted' notification widget
RUN (find /opt /usr -name notebook.js -o -name main.min.js | xargs sed -i -e 's|if (check_last_modified)|if (false)|') \
 &&  (find /opt /usr -name notificationarea.js -o -name main.min.js | xargs sed -i -e 's|this.init_trusted_notebook_notification_widget();||')


# --------
# the ipythontutor magic
RUN pip install ipythontutor
