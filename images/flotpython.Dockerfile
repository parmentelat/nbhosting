# xxx would make sense to use some fix version some day
FROM jupyter/scipy-notebook:latest

# bioinfo uses python2
#RUN /bin/bash -c "source /opt/conda/bin/activate python2 && conda install -y mpld3"
# but we might want to run python3
#RUN conda install -y mpld3

# disable these widgets as otherwise they cause the 'Widgets' submenu in the menubar
# to appear again even though we turn it off in custom.js
RUN jupyter nbextension disable jupyter-js-widgets/extension
