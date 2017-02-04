# Plan

## issue P1 - customize (1) - `jupyter_notebook_config.py`

* autosave
  * want to set to 20s for the cases where jupyters get killed on timeout
  * an attempt is made in custom.js
  * does not seem to work too well though, or needs more tests ...

## ***issue P1 - customize (2) (`js` + `css`)***

* needs more thorough checks (apparently we can change cell type !)
* partly addressed (although clearly cosmetically suboptimal)
* ***Still missing*** (but second order)
  * additional menus (***Revert*** to original, ***Share*** read-only view)
  * do we need to mess with keyboard bindings as well ? 
    - proto for an Enter-based thing but it's a little awkward

## ~~issue P1 - course management UI~~

* teachers can update their course (all use the same superuser account and see all courses for now)
* ***Still missing*** (but 2nd order)
  * let admins manage courses (several styles of courses probably)

## issue P2 - define a static/ area

* we need that to serve our own static contents
  * e.g. js for stats: `timeseries`, `mg_line_brushing.js` that don't show up in cloudjs
  * but also a local css, favicon, ...

## ~~issue P3 - stop serving on port 80 altogether~~

* and redirect / onto /nbh/

#### ~~issue P3 - cookies~~ (dropped)

* investigate if cookies really are required, or if just defining baseurl could work
* a first attempt showed the behaviour of the base_url setting is not clear
* forget about that for now

# Plan - midterm

## step P4: run nbhosting as a docker container inside thermals
* probably a big disruptive step
* however we should anticipate on this one and for one thing, reinstall thermals from scratch asap so we can have a view that is not clobbered by our previous lxc setup that might come in the way.

*****

# Notes

## a test public repo

`https://github.com/jakevdp/PythonDataScienceHandbook`

## a sample URL

* what FUN is likely to send out to nbhosting

```
https://nbhosting.inria.fr/ipythonExercice/flotbioinfo/w1/en-w1-s07-c1-walking.ipynb/mary
```

* what this should be redirected to by the django app - still on 443 for nginx

```
https://nbhosting.inria.fr/8000/w1/en-w1-s07-c1-walking.ipynb?token=flotbioinfo-x-mary
```

* which gets internally (i.e. on localhost) proxied over http to

```
http://127.0.0.1:8000/notebooks/w1/en-w1-s07-c1-walking.ipynb?token=flotbioinfo-x-mary

```

* clean up before serving this URL:

```
docker stop flotbioinfo-x-mary ; docker rm flotbioinfo-x-mary ; ./del-student /nbhosting-test mary; rm -rf /nbhosting-test/logs/flotbioinfo/run-mary.log
```

* trying to get a static page using the cookie

```
curl -L -o cookielogo.png --cookie "docker_port=8000;Path=/;Max-Age=31536000" https://nbhosting.inria.fr/static/base/images/logo.png
```

* monitoring

```
logs-jupyter
logs-nginx
jour-nginx
logs-nbhosting
jour-nbhosting
jour-docker
```


## creating course

```
rm -rf /nbhosting-test/courses{-git}/flotbioinfo /nbhosting-test/logs/flotbioinfo
./init-course /nbhosting-test flotbioinfo https://github.com/parmentelat/flotbioinfo.git
cat /nbhosting-test/logs/flotbioinfo/init-course.log
ls /nbhosting-test/courses-git/flotbioinfo

./update-course /nbhosting-test flotbioinfo 
cat /nbhosting-test/logs/flotbioinfo/update-course.log
ls /nbhosting-test/courses/flotbioinfo
```

## steps for dealing with jupyter

do we need to create  config file or are all options configurable on the command line ?

## MAJOR notes

* if we start and stop docker, containers cannot be stopped or removed anymore
* BUT: when adding a student we add her to the docker group
  * I have moved from systemctl restart docker to using just reload; hopefully this will do it

* when trying to reach a notebook inside the running jupyter, URL must be prefixed by `/notebooks/` followed by a path to the actual filename
