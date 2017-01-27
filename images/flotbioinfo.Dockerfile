FROM jupyter/scipy-notebook:latest

# bioinfo uses python2
RUN /bin/bash -c "source /opt/conda/bin/activate python2 && conda install -y mpld3"
