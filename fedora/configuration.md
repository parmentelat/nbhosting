# Notes on configuration

## Current status

As of Nov. 24 2017, and commit 5ad16ea, configuring nbhosting has become substantially simpler:

* after obtaining the code through `git clone` do this

```
cd nbhosting/main
cp sitesettings.py.example sitesettings.py
```

Then edit the file with the details that describe your site specifics; you can for example

* chose to use http or https (https is almost mandatory though, see comments in the file)
* define where your certificate and key are if you go for https
* set a private `SECRET_KEY` for django
* set `DEBUG` for django
* ...

The benefit of this approach is that `sitesettings.py` is outside of git scope, and won't generate any merge conflicts. On the downside, if `sitesettings.py.example` changes, the local copy needs to be edited accordingly..
