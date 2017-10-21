# Notes on configuration

## `http` *vs* `https`

* you can run `./install.sh -d` (`d` stands for development) to run over http instead; in this case we use `nginx/nginx-https.conf` instead

## list

* until a proper config. mechanism is in place, here's a list of places in the git files that contain hard-wired data that should be more configurable
* **NOTE** that `sitesettings.py` is **not** under the git repo, that contains an exemple file instead, that you can copy into your `sitesetting.py` so that your site-specific settings won't conflict with updates in the git repo.

| file                         | search              | config for | comment             |
|------------------------------|---------------------|------------| ---------|
| `nginx/nginx-https.conf`     |  `server_name`      |  nginx  | your hostname        |
| `jupyter/jupyter_notebook_config.py` | `Content-Security-Policy` | web browser | trusted domain (typically `fun-mooc.fr`) |
|                              |                     |         | this for now is hard-wired  |
| `nbhosting/main/sitesettings.py` | `ALLOWED_HOSTS`     |  django | define your hostname(s)  |
|                              |                     |         | otherwise `Bad Request (400)`  |
| `nbhosting/main/sitesettings.py` | `SECRET_KEY`        |  django | use your own       |
| `nbhosting/main/sitesettings.py` |  `allowed_referer_domains`  | nbhosting | domain names that can redirect to here |
| `nbhosting/main/sitesettings.py` |  `allowed_devel_ips`  | nbhosting | IP's that you authorize to issue |
|                              |                     |         | /ipythonExercice/ URLS directly |
