# Fedora installation and setup

## Purpose

* this document is about setting up `nbhosting` from metal, i.e. right after a fresh
  install.
* date: originaly written in July 12 2017
* revised July 1 2019
  * based on fedora 29
* revised: January 2020
  * based on fedora 31
* revised: November 2020
  * based on fedora 33

## Requirements

Depending on the scope of your deployment, you will need

* primarily as much memory as you can get; `nbhosting` spawns one jupyter-powered
  container per tuple (student x course), so even if these are killed after a fixed amount
  of idle time (monitor's *idle* setting), that may require a substantial amount of
  memory; rule of thumb is to provision for about 200Mb of RAM per kernel (open notebook)
* in terms of disk space, 1 Tb will already lead you rather far, thanks to COW
  imaging capabilities.

## SSL

* the application can in theory run under simply `http` in devel mode, but for any real
  deployment you're going to run as an iframe-embedded site for a main site that runs
  https (like e.g. `fun-mooc.fr`). In such a case running `nbhosting` behind `http` just
  won't work, as the browser won't allow it; it is thus assumed that you have a proper
  certificate and private key available

* in case of a reinstallation
  * ***don't forget*** to back up SSL certificate and especially ***the private key***
  * which in the case of `nbhosting.inria.fr` is stored in dir `/root/ssl-certificate/`

## Packaging

`nbhosting` is designed to be easy to deploy, but it does some rather strong assumptions
 on the underlying infrastructure. In particular, it assumes that you have a **dedicated**
 fedora box for running the complete service. In this respect it has no provision for
 leveraging several physical servers. In line with this assumption, all the pieces come as
 a single monolithic bundle, that takes care of all the pieces (nginx, django in uwsgi)
 from a single point of installation and control.

## podman and its Python API

starting with 0.30, nbhosting runs on top of podman and no longer supports docker.

**at this particular point in time (June 2020)** :

* we depend on a homebrewed version of the `podman-py` module that implements the Python
  API over libpod
* that is not available at pypi yet
* so a separate installation is required
* also note that rpm podman >= 1.9.2 is required

```bash
# install podman-py from sources for now
git clone git@github.com:parmentelat/podman-py.git
cd podman-py
git checkout nbhosting
pip install .
```

## cgroups

podman can use cgroupsv2, which is the default on fedora>=31; no need to mess with
kernel-booting options (like the ones that would be required to run docker)

## umask

When updating to fedora-33, we have had to change this line in `/etc/login.defs`

```
UMASK           022
```

which was previously set to `077`; without this setting, the files created under
the `courses-git` directory were only readable by `root`, and thus unavailable to
users, which in turn would create a lot of 404 errors.

****

# disk partitioning

> ***Note*** that the choice of *btrfs* dates back to 5 years ago, with earlier
versions of docker; this is still what we use on `nbhosting.inria.fr` right now,
but we use now podman and surely there are other combinations of
(physical partitioning scheme x logical cow fs driver) that work just as well,
so feel free to pick your own choice here.


We use `btrfs` as the underlying filesystem for containers;
the requirement is thus to have `/nbhosting` mounted on a `btrfs` partition somehow.

**Note** that since the switch to using podman, this is probably no longer a hard constraint.

##### Optional Note

It might make more sense to actually cut **2 separate btrfs
partitions**, instead of a single one like it is exposed below; having
a completely separate btrfs partition for hosting the images and
containers may turn out to be more convenient, especially when a reset
is needed. Remember that it takes less than a second to create a new
btrfs filesystem on a partition, while it can take hours to properly
remove images and containers cleaning, so there's that. This being
said, the current production box on `nbhosting.inria.fr` has this
single btrfs partition scheme, so a dual-partition setup can be
considered optional. The location where container images use disk space
is hard-wired as `/nbhosting/containers`; it is configurable,
but make sure to pick the right location before building all your images.

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

* `/nbhosting/containers/`

   will be handed over to podman as its main area for storing images and snapshots, basically all the copy-on-write powered images

****

# 1-time fedora config

After a base installation of fedora, please do the following:

## install prerequisites

```bash
dnf -y install podman
dnf -y install git
```

## install podman-py

As of this writing (May 2020) podman-py is in a very early development stage;
hopefully this will be availaible through pip at some point

```bash
cd /root
git clone https://github.com/parmentelat/podman-py
cd podman-py
git checkout nbhosting
pip install -e .
```

## download `nbhosting` sources

```bash
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
cp fedora/etc/sysconfig/iptables /etc/sysconfig/iptables
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
cp fedora/etc/sudoers.d/99-nbhosting /etc/sudoers.d/
chmod 440 /etc/sudoers.d/99-nbhosting
```

## `login.defs`

check that you have UMASK set to 077 in `/etc/login.defs`

## reboot

In order to apply changes (esp. regarding selinux, and iptables)

****

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
pip3 install --upgrade pip setuptools wheel
```

Other pip-managed requirements are handled automatically when running `install.sh`

## SSL certificates

The example config has it that the SSL certificate used by the main entry point (in our
case `nbhosting.inria.fr`) be located in `/root/ssl-certificate/`.

You can of course pick any other location that you want, but you will later on need the
location of your certificate and key; in our case we installed them in:

```python
ssl_certificate = "/root/ssl-certificate/bundle.crt"
ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key"
```

## initial configuration

```bash
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

```bash
cd /root/nbhosting
./install.sh
```

that will also take care of everything, like starting the services.

## admin (create super user)

Initialize the admin superuser; this is what will allow to enter the admin web interface:

```bash
cd /root/nbhosting/django
python3 manage.py migrate
python3 manage.py createsuperuser
```

You should be good to go; point your browser at your domain name

<https://mynbhosting.example.org>

and enter with the login/password you just enabled with `createsuperuser`

## reconfiguring

# administering the system

## `nbh-manage`

There's a single command `nbh-manage` that's an entry point into all the features exposed
to the CLI; see the list with

```bash
nbh-manage help
```

this actually is the usual django's `manage.py`, but extended in the `[courses]`
and `[nbh_main]` categories. This is the tool we'll use to prepare courses and images.

****

## Preparing core images

### pull container images (step A)

```bash
podman pull  jupyter/minimal-notebook; podman pull jupyter/scipy-notebook
```

This will fetch at dockerhub the 2 images that are used to create our own core images

### build core images (step B)

```bash
nbh-manage build-images
```

This will rebuild images `nbhosting/minimal-notebook` and
`nbhosting/scipy-notebook` on top of the publically available ones that we pulled in step
A.

## Managing courses

### course initialisation (step 1: bind to a git repo)

Create a course named `python3` from git repo `https://github.com/flotpython/course.git`

```bash
nbh-manage course-create python3 https://github.com/flotpython/course.git
```

**Note** if you want to attach that course to an image whose name is **not the course name**, you can add a `-i` or `--image` option (can be tweaked later of course)

```bash
nbh-manage course-create -i nbhosting/scipy-notebook python3 https://github.com/flotpython/course.git
```

### course image (step 2 : build course image)

The image name to use with a course is modifiable in the web UI - you
need staff privileges of course.

#### option 1 : use a core image

nbhosting comes with predefined images, that are built on top of publically
available images (see step B above). If you'd like your course to use one of
these, use e.g. `nbhosting/minimal-notebook` as the image name for this course.

***Note*** that it is **not recommended** to use dockerhub images *as is*, as it will
cause very poor overall performance. FYI the recipes to build our core images are located in the `images` subdir in the git repo.

#### option 2 : piggyback

If your nbhosting instance already hosts a course, say `python3`, and you want to host course `mycourse` with the same image as `python3`, you can just use that as your image name.

#### option 3 : your own image

Otherwise, your image name should match the course name (which is the default of course), and you can rebuild that image from the shell with

```bash
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
nbh-manage course-pull mycourse
```

## Web UI

The breadcrumb track is designed to give a staff admin access to functions targetting
administrative (red buttons) or regular consultation (blue buttons) features.

![crumbs](crumbs.png)

So for example, you can trigger updates from git, and image builds, from the web UI at the
(red) course page.

## course settings (optional)

### what ?

There are a few settings available for a course; as of this writing:

* a boolean `autopull` flag; when enabled, nbhosting will pull from git every hour or so;
* image name to use; the default is the coursename, so `flotpython` looks for image `flotpython`; however images are big and tedious to build, so you could want to share another course's image
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

This is configurable from the Web UI; go the the course management page, and click the
orange `edit details for yourcoursename` button

#### static mappings
static mappings allow you to define symlinks that work from anywhere in the notebooks
tree; for example, if you define the following 2 mappings

```text
data -> data
rise.css -> media/rise.css
```

then in every student work dir (i.e. every directory that contains at least one student
notebook), the platform will create symbolic links named `data` and `rise.css`, that point
at **read-only** snapshots of `data` and `media/rise.css`, from the git repo toplevel.

For legacy reasons, the default static mappings are defined as

```text
data -> data
media -> media
```

but can be redefined in each course git repo in `nbhosting/static-mappings` - with the
format used above.

#### tracks

when run in classroom mode, we have no MOOC structure to guide our students, so the
following mechanism allows to define some structuration. This is done through the notion
of **tracks**.

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
* `nbh-django`
  * the django app runs inside nginx through uwsgi
* `nbh-monitor`
  * monitor performs housecleaning (kill idle containers), and on the side also gathers raw data for statistics

## logs

Additional logs go into

* `$NBHROOT/logs/nbhosting.log`
* `$NBHROOT/logs/monitor.log`
* `$NBHROOT/logs/nginx-{error,access}.log`
* also each container can be probed for its logs
  * `podman logs` *`thecoursename`*`-x-`*`thestudenthash`*

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

# podman as a replacement to docker

We chose to drop docker; the docker daemon is acting as a bottleneck
and impeds performance; plus, it's becoming harder and harder to get
`docker-ce` distributions, and this gets in the way.

So welcome podman, that is available right out of the vanilla repo on
f32+ (nbhosting might not work well on top of podman on f31) ; it does
support cgroup-v2, and has a compatible CLI interface; so add to that
the fact that our fedora-29 deployment is exhibiting really weird and
odd behaviour, replacing docker with podman is definitely worth it.

One can even (not needed) install the `podman-docker` rpm so that you
can keep on running the `docker` command and talk to podman instead.

# upgrading

## upgrading nbhosting

```bash
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

In this case, you need to identify the 2 new variables, and define
them in your `sitesettings.py` (even if you are fine with the defaults
as set in the example file)

## note on fedora upgrades

If you upgrade to a more recent fedora, as always `dnf` will take care
of the packages that it knows about, but **won't automatically install
the `pip` dependencies, that need to be reinstalled manually**

For example, when upgrading from say f31 to f32, python3 will move from
3.7 to 3.8; so pip dependencies will restart from scratch;
`install.sh` should do all the heavylifting in this case, but check
also for the installation pf `podman-py` that will need a dedicated manual
intervention as well.

## note on upgrading from docker to podman

This one-shot move might be a little more awkward than usual; double-check

* that you rebuild all images after having tweaked `podmanroot`
* optionnally that you clean up the previous containers image location
  (`/nbhosting/dockers` by default)
