# Notes on configuration

## Current status

As of Nov. 24 2017, and commit 5ad16ea, configuring nbhosting has become substantially simpler:

* after obtaining the code through `git clone` do this

```
cd django/nbh_main
cp sitesettings.py.example sitesettings.py
```

Then edit the file with the details that describe your site specifics; you can for example

* chose to use http or https (https is almost mandatory though, see comments in the file)
* define where your certificate and key are if you go for https
* set a private `SECRET_KEY` for django
* set `DEBUG` for django
* ...

The benefit of this approach is that `sitesettings.py` is outside of git scope, and won't generate any merge conflicts. On the downside, if `sitesettings.py.example` changes, the local copy needs to be edited accordingly..

## Updates

At this point though, the contents of the example file is **not loaded as defaults**, and so you **must** define all the expected variables in your `sitesettings.py`. This means that some care might be needed when updating to a more recent release. Consider the following scenario:

* you install as described above; you end up with 10 variables in your `sitesettings.py` file
* a month later, you pull a new release that has 12 variables in `sitesettings.py.example`

In this case, you need to identify the 2 new variables, and define them in your `sitesettings.py` (even if you are fine with the defaults as set in the example file)
