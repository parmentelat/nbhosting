# Configuration file for jupyter-notebook under nbhosting
#
# derived from the file found in image jupyter/scipy-notebook as of jan. 27 2017
# in /home/jovyan/.jupyter/jupyter_notebook_config.py
#
# --------------------

c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False

# allow other websites to embed as a frame
# https://github.com/jupyter/notebook/issues/1256

c.NotebookApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors https://*.fun-mooc.fr ;",
    }
}
