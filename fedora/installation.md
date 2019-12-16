# Fedora installation and setup

## Purpose

* this document is about setting up `nbhosting` from metal, i.e. right after a fresh install.
* date: July 12 2017 - revised July 1 2019
* based on fedora 29


## Requirements

Depending on the scope of your deployment, you will need

* primarily as much memory as you can get; `nbhosting` uses docker to spawn one
  jupyter-powered container per tuple (student x course), so even if these are killed
  after a 15 minutes-ish amount of idle time, that may require substantial amount;
* in terms of disk space, 1 Tb will already lead you rather far, thanks to docker's
  imaging capabilities.

## SSL

*  the application can in theory run under simply `http` in devel mode, but for any real
   deployment you're going to run as an iframe-embedded site for a main site that runs
   https (like e.g. `fun-mooc.fr`). In such a case running `nbhosting` behind `http` just
   won't work, as the browser won't allow it; it is thus assumed that you have a proper
   certificate and private key available

* in case of a reinstallation
  * ***don't forget*** to back up SSL certificate and especially ***the private key***
  * which in the case of ` nbhosting.inria.fr` is stored in dir `/root/ssl-certificate/`

## Packaging

`nbhosting` is designed to be easy to deploy, but it does some rather strong assumptions
 on the underlying infrastructure. In particular, it assumes that you have a **dedicated**
 fedora box for running the complete service. In this respect it has no provision for
 leveraging several physical servers. In line with this assumption, all the pieces come as
 a single monolitihic bundle, that takes care of all the pieces (nginx, django in uwsgi)
 from a single point of installation and control.

****

# disk partitioning

We use `btrfs` as the underlying filesystem for docker; the requirement is thus to have
`/nbhosting` mounted on a `btrfs` partition somehow.


##### Optional Note

It might make more sense to actually cut **2 separate btrfs partitions**, instead of a
single one like it is exposed below; having a completely separate btrfs partition for
hosting the docker images and containers may turn out to be more convenient, especially
when a reset is needed. Remember that it takes less than a second to create a new btrfs
filesystem on a partition, while it can take hours to properly remove images and
containers using docker one by one, so there's that. This being said, the current
production box on `nbhosting.inria.fr` has this single btrfs partition scheme, so a
dual-partition setup can be considered optional. The location where docker images uses
disk space is hard-wired as `/nbhosting/dockers` (and, as of this writing, is not
reconfigurable).


## system *vs* application

You should reserve some reasonable space for your system install, so typically you would
cut 2 main partitions (ignoring the other OS-oriented details):

* `/` should be mounted on a (for example) 30 Gb partition (can be either btrfs or regular ext4)
* `/nbhosting` mounted on a `btrfs` partition that spans the rest of the (for example) 1 Tb hard drive.

Here is what can be observed on our production and devel boxes:

```bash
root@devel ~ (master *) #
df -hT / /nbhosting /boot
Filesystem     Type   Size  Used Avail Use% Mounted on
/dev/sda3      btrfs  1.1T   43G  1.1T   4% /
/dev/sda3      btrfs  1.1T   43G  1.1T   4% /nbhosting
/dev/sda1      ext4   976M  106M  804M  12% /boot
```

```bash
root@production ~ (master *) #
df -hT / /nbhosting /boot
Filesystem     Type   Size  Used Avail Use% Mounted on
/dev/sda3      ext4   271G   18G  239G   7% /
/dev/sdb       btrfs  9.9T   90G  9.7T   1% /nbhosting
/dev/sda1      ext4   190M  125M   52M  71% /boot
```

## how `nbhosting` uses this space

* `/nbhosting/courses-git/`

    is where we create git repo clones, used as a basis for exposing contents to the containers
* `/nbhosting/courses/`

   contains an extract of the git repo with all found notebooks
* `/nbhosting/students`

   is the root for the homedirectories created for students as they show up
* **others subdirs**

  like `logs`, for logs, `raw` for collecting events and counts later processed as statistics, ...

## valuable data

The data that should be backed up is the one in

* `/nbhosting/students`

   has the copies made by the students, together with their `.nbautoeval` trace files

* `/nbhosting/raw`

  is designed to be low-to-mid noise, and to take reasonable space; it is enough to reconstruct all the statistics displayed in the web pages.

* `/nbhosting/local`

  is the place where the admin can write stuff to supersede what comes with each course repo in their `nbhosting/` subdir; like `Dockerfile`, `tracks.py` and such other customizations

## disposable data

* `/nbhosting/dockers/`

   will be handed over to docker as its main area for storing images and snapshots, basically all the copy-on-write powered images

****

# 1-time fedora config

After a base installation of fedora, please do the following:

## install docker-ce 

**Warning** the docker stack as published by fedora has stopped being upgraded a few years
back, make sure to use docker-ce as published by docker

```
dnf -y install dnf-plugins-core
dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
dnf install docker-ce docker-ce-cli containerd.io
```

## install git and download `nbhosting` sources

```
dnf -y install git
cd /root
git clone https://github.com/parmentelat/nbhosting.git
```

## iptables vs firewalld

* we want to use a static `iptables` config, and ***not firewalld*** that will just screw it all up for us

```bash
dnf install -y iptables-services
systemctl mask firewalld.service
systemctl enable iptables.service
cd /root/nbhosting
cp etc/sysconfig/iptables /etc/sysconfig/iptables
```

## turn off SElinux

likewise, we need to turn off SElinux

```bash
cd /root/nbhosting
cp etc/selinux/config /etc/selinux/config
```

## `sudo` 

* it is required that `sudo` allows non-tty apps to issue calls to `sudo`; by default on fedora, it is the case, but it turns out our local IT used to have a policy in place that requires a terminal (see `requiretty` as a sudo configuration clause). To address this, consider creating the following file:

```bash
cd /root/nbhosting
cp etc/sudoers.d/99-nbhosting /etc/sudoers.d/
chmod 440 /etc/sudoers.d/99-nbhosting
```

## docker setup
```
systemctl enable docker
```

## reboot

In order to apply changes (esp. regarding selinux, and iptables)

*************************

# application install

## packages / dependencies

* ***NOTE*** Be careful to **not install `python3-django` from rpm** as this might give a
  too old version of Django. That was true as of end 2018, might no longer be an issue
  now.

* FYI, see `capture-versions.sh`  and files named `VERSIONS*` in the present subdir, that
  give more details of what was running on nominal deployments, and on the actual split
  between what was installed with `dnf` and what comes from `pip`

To install third-party packages that `nbhosting` depends on:

```bash
dnf -y install python3
dnf -y install nginx
dnf -y install uwsgi uwsgi-plugin-python3
```

```bash
pip3 install --upgrade pip setuptools
pip3 install --upgrade Django django-extensions
pip3 install jsonpickle nbformat jupytext
# for nbh-monitor
pip3 install aiohttp docker
```


## SSL certificates

The default config has it that the SSL certificate used by the main entry point (in our case `nbhosting.inria.fr`) be located in `/root/ssl-certificate/`. 

You can of course pick any other location that you want, but you will later on need the
location of your certificate and key; in our case we installed them in:

```
ssl_certificate = "/root/ssl-certificate/bundle.crt"
ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key"
```

## initial configuration

```
cd /root/nbhosting/django/nbh_main
cp sitesettings.py.example sitesettings.py
```

The benefit of this approach is that `sitesettings.py` is outside of git's scope, and
won't generate any merge conflicts when upgrading later on. On the downside, if
`sitesettings.py.example` changes, the local copy needs to be edited accordingly..

Then edit the file with the details that describe your site specifics; you can for example

* chose to use http or https (https is almost mandatory though, see comments in the file)
* define where your certificate and key are if you go for https
* set a private `SECRET_KEY` for django
* set `DEBUG` for django
* define the frontends that you accept to be an iframe of,
* ...


## applying a configuration

Every time that you change `sitesettings.py`, you need to apply them by doing

```
cd /root/nbhosting
./install.sh
```

that will also take care of everything, like starting the services.


## admin (create super user)

Initialize the admin superuser; this is what will allow to enter the admin web interface:

```
cd /root/nbhosting/django
python3 manage.py migrate
python3 manage.py createsuperuser
```

You should be good to go; point your browser at your domain name

https://mynbhosting.example.org

and enter with the login/password you just enabled with `createsuperuser`


## reconfiguring



# administering the system

## `nbh-manage`

There's a single command `nbh-manage` that's an entry point into all the features exposed
to the CLI; see the list with

```
nbh-manage help
```

this actually is the usual django's `manage.py`, but extended in the `[courses]`
and `[nbh_main]` categories. This is the tool we'll use to prepare courses and images.

****

## Preparing core images

### pull docker images (step A)

```
docker pull  jupyter/minimal-notebook; docker pull jupyter/scipy-notebook
```

This will fetch at dockerhub the 2 images that are used to create our own core images

### build core images (step B)

```
nbh-manage build-core-images
```

This will rebuild docker images `nbhosting/minimal-notebook` and
`nbhosting/scipy-notebook` on top of the publically available ones that we pulled in step
A.


## Managing courses

### course initialisation (step 1: bind to a git repo)

Create a course named `python3` from git repo `https://github.com/flotpython/course.git`

```bash
nbh-manage course-create python3 https://github.com/flotpython/course.git
```

**Note** if you want to attach that course to a docker image whose name is **not the course name**, you can add a `-i` or `--image` option (can be tweaked later of course)

```bash
nbh-manage course-create -i nbhosting/scipy-notebook python3 https://github.com/flotpython/course.git
```

### course image (step 2 : build course image)

The docker image name to use with a course is modifiable in the web UI - you
need staff privileges of course. 

#### option 1 : use a core image

nbhosting comes with predefined images, that are built on top of publically
available images (see step B above). If you'd like your course to use one of
these, use e.g. `nbhosting/minimal-notebook` as the docker image name for this course.

***Note*** that it is **not recommended** to use dockerhub images *as is*, as it will
cause very poor overall performance. FYI the recipes to build our core images are located in the `images` subdir in the git repo.

#### option 2 : piggyback

If your nbhosting instance already hosts a course, say `python3`, and you want to host course `mycourse` with the same image as `python3`, you can just use that as your docker image name.

#### option 3 : your own image

Otherwise, your docker image name should match the course name (which is the default of course), and you can rebuild that image from the shell with

```
nbh-manage course-build-image mycourse
```

* this assumes a `Dockerfile` has been written for that course; this can be either

  * in the course git repo, under `nbhosting/Dockerfile` or (re)defined locally,
    in `nbhosting`'s root directory (default for that is `/nbhosting`), in a
    file called `local/mycourse/Dockerfile`


### refreshing course contents

Whenever you push a change to the master course git repo (e.g. on github), there is a need
to tell nbhosting to pull that change so it is aware. Two options are available for that

* you can turn on autopull mode; for that, use the web UI (see below), it will cause nbhosting to pull on an hourly basis
* otherwise you will need to pull the course contents manually, through the Web UI again, or from the command line with

```bash
nbh-manage course-pull-from-git mycourse
```

## Web UI

The breadcrumb track is designed to give a staff admin access to functions targetting
administrative (red buttons) or regular consultation (blue buttons) features.

![](crumbs.png)

So for example, you can trigger updates from git, and image builds, from the web UI at the
(red) course page.

## course settings (optional)

### what ?

There are a few settings available for a course; as of this writing:

* a boolean `autopull` flag; when enabled, nbhosting will pull from git every hour or so;
* docker image name to use; the default is the coursename, so `flotpython` looks for image `flotpython`; however images are big and tedious to build, so you could want to share another course's image
* students that are considered *staff*; corresponding hashes will be ignored when building usage statistics

By experience, these first 3 settings seem to make more sense on a nbhosting
deployment basis; the dev and prod boxes will not necessarily align on these.

From that same staff course page, you can also see

* list of static mappings; see below
* sectioning and tracks; see below

These last 2 settings, on the other hand, seem to depend on the git repo structure only,
and that is why there are defined **from (files in) the course repo itself**.

### how ?

#### autopull, image and staff

This is configurable from the Web UI; go the the course management page, and click the orange `edit details for yourcoursename` button


#### static mappings
static mappings allow you to define symlinks that work from anywhere in the notebooks tree; for example, if you define the following 2 mappings

```
data -> data
rise.css -> media/rise.css
```

then in every student work dir (i.e. every directory that contains at least one student notebook), the platform will create symbolic links named `data` and `rise.css`, that point at **read-only** snapshots of `data` and `media/rise.css`, from the git repo toplevel.

For legacy reasons, the default static mappings are defined as

```
data -> data
media -> media
```

but can be redefined in each course git repo in `nbhosting/static-mappings` - with the format used above.

#### tracks

when run in classroom mode, we have no MOOC structure to guide our students, so
the following mechanism allows to define some structuration. This is done through the notion of **tracks**.

A track has a name, and defines essentially sections of notebooks. Each course
is expected to expose at least one default track; unless redefined, this default
track is built from the filesystem structure: one section per directory, with a
name that matches the directory name.

A course can expose several tracks; it could be for example an easy
track and a deeper track; or a course track and an exercices track; or
a french and an english track; or whatever other standpoints that can
be built from the course raw material.

A course can define his own tracks, by writing a Python module in
`nbhosting/tracks.py`; see [an example for
flotpython/slides](https://github.com/flotpython/slides/blob/master/nbhosting/tracks.py).
The ` tracks()` function is expected to return a dictionary, whose
keys are taken as the names for all available tracks.


### when ?

Beware that some settings are used at **container-creation** time; meaning that if a
student has come at least once, her container exists and the course settings will be
mostly ignored.

Same goes of course if a change is made to the course image (like, adding a Python
library).

This being said, a stopped container can be safely removed manually, causing it
to be re-created the next time a student shows up. But tearing down thousands of
containers can be time-consuming and create a big load on the box. To alleviate
for that, the monitor is instructed to remove containers that have not been used
in a fixed amount of time - typically a couple weeks. It also removes containers
that rely on an older version of the image.

****

# Operations

## services

as far as `systemd` and `journactl` are concerned:

* `nginx`
  * fedora's nginx service as-is
* `nbh-uwsgi`
  * the django app runs inside nginx through uwsgi
* `nbh-monitor`
  * monitor performs housecleaning (kill idle containers), and on the side also gathers raw data for statistics

## logs

Additional logs go into

* `$NBHROOT/logs/nbhosting.log`
* `$NBHROOT/logs/monitor.log`
* `$NBHROOT/logs/nginx-{error,access}.log`
* also each docker container can be probed for its logs
  * `docker logs flotpython-x-thestudentid`

## visual stats

* https://nbhosting.inria.fr/staff/ is the - very rough - front-end for the django app
* it targets only the admin of course, and the login/passwd for the admin user was created above (see `manage.py createsuperuser`)
* main page is `https://nbhosting.inria.fr/staff/courses`; each course comes with its stats page; probably subject to changes, so you'd better see for yourself, but as of now:
  * number of registered students
  * number of students per notebook, over time
  * number of notebooks read
  * number of containers/kernels
  * disk space
  * cpu load

## rain check
* it is also possible to open any of the notebooks: go to the admin page for a given
  course; clicking any of the notebooks will open it as if opened by a student whose name
  is `anonymous`.
* this is a convenient way to check the course is up and running - in particular, make
  sure you have built the image for that course !


# upgrading

## upgrading nbhosting

```
cd /root/nbhosting
git pull
./install.sh
```

***Caveat***

Be aware that the contents of the example file (`sitesettings.py.example`) 
is **not loaded as defaults**, and so you **must** define all the expected variables 
in your `sitesettings.py`. This means that some care might be needed when updating
to a more recent release. Consider the following scenario:

* you install as described above; 
  you end up with 10 variables in your `sitesettings.py` file
* a month later, you pull a new release that has 12 variables
  in `sitesettings.py.example`

In this case, you need to identify the 2 new variables, and define them in your `sitesettings.py` (even if you are fine with the defaults as set in the example file)


## note on fedora upgrades

If you upgrade to a more recent fedora, as always `dnf` will take care of the packages
that it knows about, but **won't automatically install the `pip` dependencies, that need
to be reinstalled manually**. 

## note on upgrading to 0.24

A special case has to be considered when upgrading from a release <= 0.23 to another >= 0.24

In a nutshell, there is a change of policy between these 2 releases :
* in 0.23 and below, containers are created on a need-by-need basis, and after some idle
  time - typically 30 minutes - those containers are killed, but not removed; actually
  they are removed after a much longer delay of inactivity - think 2 weeks;
* in 0.24 and above on the contrary, containers are created when needed, but immediately
  removed after the short idle timeout

To put it in other words, this means that in nominal mode :
* in 0.23, `docker ps -a` may have a long list of pending containers, while
* in 0.24, `docker ps -a` is essentially empty, except for the occasional container that
  is being removed at that time
  
When upgrading from 0.23 to 0.24: the new code has provisions to deal with the case where
the required container exists and is stopped (which means there is a lingering sequel from
0.23); however operations should not rely on that, particularly if a vast number of
lingering containers were still idling about. 

So the recommended way to upgrade is to start with running the following command; note
that this assumes that your docker deployment has no other purpose than serving nbhosting,
as it removes **ALL** stopped containers; adapt as needed if that's not the case.

Note that this cleanup command **can be launched with the nbhosting service still running**;
it is likely to take quite some time though, depending on the number of stopped containers;   
you can estimate that time by running `docker ps -a | wc -l` to figure how many they are.

For your information, on `nbhosting.inria.fr` we had about 700 lingering containers, and
the cleanup has taken a few hours. 

Also note that this command, provided again that docker only serves nbhosting, is
completety safe to run anytime in advance, and as many times as needed, since it is
idempotent, so it can be anticipated.

```
### this should be run before upgrading to 0.24
### it can be safely run while the service is up and running
###
### purpose is to remove all stopped containers
### note that this command may take a loooooog time to complete

docker ps -aq --no-trunc -f status=exited | xargs docker rm
```

Once this has completed, you can safely upgrade the usual way :
```
git pull
./install.sh
```

## note on upgrading to 0.25

First, please note that as part of 0.25, the `systemd` service that used to be called
`nbh-uwsgi` is now more simply `nbh-django`, which is easier to remember - see issue #103

Some cleanup has been done in the `sitesettings.py` area; 
you will **need to** review your own file according to the following changes

* `log_subprocess_stderr` has the same meaning but is renamed as 
  `DEBUG_log_subprocess_stderr`; it is recommended to move its definition close 
  to the definition of the plain django `DEBUG` variable - see issue #106
* define the 2 new variables `monitor_idle` and `monitor_period` (in minutes)
  - see issue #104
* define new variable `dockerroot`, which ought to be `/nbhosting/dockers` 
  if you are upgrading since that was previously the hard-wired default - see issue #105

Generally speaking, a good way to approach these changes is to compare

* `sitesettings.py.example` that comes with the git repo and reflects 
  what your file should look like, and
* `sitesettings.py` that contains your own settings.

These two files should be almost identical, except of course 
for the actual values for your site.
