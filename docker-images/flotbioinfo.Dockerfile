# scipy is really big, let's try something smaller
#FROM jupyter/scipy-notebook:latest
FROM jupyter/base-notebook:latest

# bioinfo used to use python2
#RUN /bin/bash -c "source /opt/conda/bin/activate python2 && conda install -y mpld3"
# but that's not in base-notebook, and python2 is not the point
# it should work in both environments anyway..
# but we might want to run python3
RUN conda install -y mpld3

# disable these widgets as otherwise they cause the 'Widgets' submenu in the menubar
# to appear again even though we turn it off in custom.js
RUN jupyter nbextension disable jupyter-js-widgets/extension
