# Notes on configuration

## `http` *vs* `https`

* you can run `./install.sh -d` (`d` stands for development) to run over http instead; in this case we use `nginx/nginx-https.conf` instead

## list

* until a proper config. mechanism is in place, here's a list of places in the git files that contain hard-wired data that should be more configurable

| file                         | search              | config for | comment             |
|------------------------------|---------------------|------------| ---------|
| `nginx/nginx-https.conf`     |  `server_name`      |  nginx  | your hostname        |
| `nbhosting/main/settings.py` | `ALLOWED_HOSTS`     |  django | define your hostname(s)  |
|                              |                     |         | otherwise `Bad Request (400)`  |
| `nbhosting/main/settings.py` |    `SECRET_KEY`     |  django | use your own       |
| `nbhosting/main/settings.py` |  `allowed_incoming_ips`       |    nbhosting | IP's that you authorize   |
|                              |                     |         | typically FUN and your own trusted ones |

