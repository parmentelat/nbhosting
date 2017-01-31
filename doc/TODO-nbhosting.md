# Plan

## ~~Issue P1 - X-frame-options~~

* X-frame-options is set to SAMEORIGIN; need to figure whether nginx or django is the culprit

## ~~Issue P1 - Content-Security-Policy~~

* actual URLs from FUN don't seem to make it up the stack to django
* defined proper header in jupyter config (for the tornado subapp)

## ~~milestone (pending)~~

* the inria/demo course #2 has 2 notebooks on 2 separate courses (flotpython / flotbioinfo)

## ~~issue P1 - customize (1) - `jupyter_notebook_config.py`~~

* ***WARNING*** that the config file is already present in the docker image !!
* it does things like running on all IP addresses (`.ip = '*'`) **AND* it generates a self-signed certificate which is probably what takes so long !?!

```
# docker exec flotbioinfo-x-mary ls -l /home/jovyan/.jupyter/jupyter_notebook_config.py
-rw-rw-r-- 1 jovyan users 1205 Jan  2 19:55 /home/jovyan/.jupyter/jupyter_notebook_config.py
# docker exec flotbioinfo-x-mary grep -i notebookapp /home/jovyan/.jupyter/jupyter_notebook_config.py
c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
    c.NotebookApp.certfile = pem_file
```

## ~~issue P1 - some sort of packaging~~ 

* workflow is git push -> git pull -> install.sh

## ***issue P1 - customize (2) (`js` + `css`)***

* partly addressed (although clearly cosmetically suboptimal)
* ***Still missing***
  * additional menus (revert to original, share read-only view)
  * unclear if something special is required to get the notebook to reconnect to its kernel if/when the docker instance get killed
  * do we need to mess with keyboard bindings as well ? 
    - proto for an Enter-based thing but it's a little awkward

## issue P1 - have some logs

* create a DB with events like 
  * `open(course, student, notebook, time)`
  * `close(course, student)` 

## ~~issue P1 - course management UI~~

* let teachers update their course
* let admins manage courses (several styles of courses probably)

## ~~issue P2 - not all notebooks start in [wW]*~~

esp. datascience handbook at https://github.com/jakevdp/PythonDataScienceHandbook

this convention clearly is in the way.

## issue P2 - need some authentication to manage courses

## issue P2 - how often does stuff get saved ?

* this post [https://groups.google.com/forum/#!topic/jupyter/DGCKE5fS4kQ]()
* suggests to use

```
events.on("notebook_loaded.Notebook", function () {
    IPython.notebook.minimum_autosave_interval = 10; // - 0 to disable autosave
```
* observed on my MAC with a flotpython exo - suggests it's in milliseconds

```
Jupyter.notebook.minimum_autosave_interval
120000
```
## issue P1 - checking for idle jupyters

#### FLO+BEN approach

* crontab a job that kills docker instances
* in this case we'd need to tweak the port allocation mechanism so as to avoid ports already allocated to suspended dockers
  
#### can we find something better ?

* like tweaking the frequency for auto-save (which might be a good idea anyways)
* and then just monitor the work/ directories (maybe .ipynb-checkpoints or whatever the actual name is)

## ~~issue P3 - cookies~~ (dropped)

* investigate if cookies really are required, or if just defining baseurl could work
* a first attempt showed the behaviour of the base_url setting is not clear
* forget about that for now

## issue P2: custom images

* create custom docker image with a few additions in pip3:
  * e.g. mpld3 for flotbioinfo
* come up with some sort of workflow for when this need arises

## issue P2 - docker rm fragile

* `docker rm` fails with Device busy from time to time 
* Hopefully this sohuld be OK now with ``btrfs`` 

# Plan - midterm

## step P4: run nbhosting as a docker container inside thermals
* probably a big disruptive step
* however we should anticipate on this one and for one thing, reinstall thermals from scratch asap so we can have a view that is not clobbered by our previous lxc setup that might come in the way.

## step P3:
* gather data for stats

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
