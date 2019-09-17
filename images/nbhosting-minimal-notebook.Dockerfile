# --------
# using scipy, it's kinda big but that should not be a problem
# base-notebook lacks at least numpy, widgets, so...
FROM jupyter/minimal-notebook:latest


# --------
# for interfacing with nbhosting, we need this startup script in all images
# and we need to be root again for installing stuff
USER root
COPY start-in-dir-as-uid.sh /usr/local/bin

# --------
# factorizing preparation steps, that are common to
# all our images (minimal-notebook and scipy-notebook for now)

ADD nbhosting-image-root.sh /root/nbhosting-image-root.sh
RUN bash /root/nbhosting-image-root.sh

USER jovyan

ADD nbhosting-image-jovyan.sh /home/jovyan/nbhosting-image-jovyan.sh
RUN bash /home/jovyan/nbhosting-image-jovyan.sh

USER root