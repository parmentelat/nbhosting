# Notes on configuration

## Current status

As of Nov. 23 2017, configuring nbhosting has become substantially simpler:

* after obtaining the code through `git clone` do this

```
cd nbhosting/main
cp sitesettings.py.example sitesettings.py
```

Then edit the file with the details that describe your site specifics; you can for example

* chose to use http or https (https is almost mandatory though, see comments in the file)
* define where your certificate and key are if you go for https
* set a private `SECRET_KEY` for django
* ...

The benefit of this approach is that `sitesettings.py` is outside of git scope, and won't generate any merge conflicts. On the downside, if `sitesettings.py.example` changes, the local copy needs to be edited accordingly..

## Remaining stuff

There currently remains a couple settings here and there that could fruitfully be taken into account in `sitesettings` instead of the way they are now:

#### devel mode: `./install.sh -d`

* you can run `./install.sh -d` (`d` stands for development); this causes django to run in debug mode (set `DEBUG = True` in `settings.py`); should be replaced with e.g. `sitesettings.DEBUG`

#### `Content-Security-Policy`

there remains this setting here to take care of some day:

| file                         | search              | config for | comment             |
|------------------------------|---------------------|------------| ---------|
| `jupyter/jupyter_notebook_config.py` | `Content-Security-Policy` | web browser | trusted domain (typically `fun-mooc.fr`)  this for now is hard-wired  |
