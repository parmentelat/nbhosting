# xxx would make sense to use some fix version some day
FROM jupyter/scipy-notebook:latest

# disable these widgets as otherwise they cause the 'Widgets' submenu in the menubar
# to appear again even though we turn it off in custom.js
RUN jupyter nbextension disable jupyter-js-widgets/extension
