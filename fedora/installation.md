# Fedora installation and setup

* this document is about setting up `nbhosting` from metal, i.e. right after a fresh install.
* date: July 12 2017
* based on fedora 25
* **SSL certificates**: in case of a reinstallation:
  * ***don't forget*** to back up SSL certificate and especially ***the private key***
  * this is stored in dir `/root/ssl-certificate/`

# see also

* companion file `configuration.md` is an attempt at describing all the places where changes can be needed

****

# disk partitioning

## WARNING

**Something to think about before setting up a production box**:
it might make more sense to actually cut **2 separate btrfs partitions**, instead of a single one like it is exposed below; having a completely separate btrfs partition for hosting the docker images and containers may turn out to be more convenient, especially when a reset is needed. Remember that it takes less than a second to create a new btrfs filesystem on a partition, while it can take hours to properly remove images and containers using docker one by one, so there's that.


## system *vs* application

The requirement is to have `/nbhosting` mounted on a `btrfs` partition somehow.

Here's the choice that I made with the fedora installation program after selecting the `btrfs` layout:

![partitioning](partitioning.png) .

On `thermals.inria.fr` as of the setup in July 2017:

```
[root@thermals ~]# df -hT
Filesystem     Type      Size  Used Avail Use% Mounted on
devtmpfs       devtmpfs  126G     0  126G   0% /dev
tmpfs          tmpfs     126G     0  126G   0% /dev/shm
tmpfs          tmpfs     126G  1.9M  126G   1% /run
tmpfs          tmpfs     126G     0  126G   0% /sys/fs/cgroup
/dev/sda3      btrfs     1.1T  1.4G  1.1T   1% /
/dev/sda3      btrfs     1.1T  1.4G  1.1T   1% /nbhosting
tmpfs          tmpfs     126G  4.0K  126G   1% /tmp
/dev/sda1      ext4      976M   98M  811M  11% /boot
tmpfs          tmpfs      26G     0   26G   0% /run/user/0
```
## how `nbhosting` uses this space

* `/nbhosting/dockers/`

   will be handed over to docker as its main area for storing images and snapshots, basically all the copy-on-write powered images
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

* Worth being mentioned as well in this area are the various dockerfiles, that I assume are stored in the `nbhosting` git repo under `docker-images`, but well, technically this is important data as it describes the contents of each course image.

****

# fedora configs

Notes

* `/etc/sysconfig/docker` is the place where we define `/nbhosting/dockers` as being `docker`'s workspace
* we want to use a static `iptables` config, and ***not firewalld*** that will just screw it all up for us
* likewise, we need to turn off SElinux
* it is required that `sudo` allows non-tty apps to issue calls to `sudo`; by default on fedaora, it is the case, but it turns out our local IT has a policy in place that requires a terminal (see `requiretty` as a sudo configuration clause). To address this, consider creating the following file (*it puzzles me that `install.sh` does not do it, it might just not be needed any more...*)

```
# cat /etc/sudoers.d/99-nbhosting
Defaults !requiretty
```

## ssh
After raw install of fedora, do the usual:

* enable root access via ssh
* disable password authentication for sshd

## iptables vs firewalld

```
dnf install -y iptables-services
systemctl mask firewalld.service
systemctl enable iptables.service
```

## install git and docker

```
dnf -y install git docker
cd /root
git clone https://github.com/parmentelat/nbhosting.git
```

## fedora basics


```
cp etc/sysconfig/iptables /etc/sysconfig/iptables
cp etc/selinux/config /etc/selinux/config
cp etc/sudoers.d/99-nbhosting /etc/sudoers.d/
chmod 440 /etc/sudoers.d/99-nbhosting
```

## docker setup
```
sed -i -f etc-sysconfig-docker.sed /etc/sysconfig/docker

systemctl enable docker
systemctl start docker
```

## reboot

In order to apply changes (esp. regarding selinux, and iptables)

*************************

# application install

## packages / dependencies

***IMPORTANT NOTES*** about python libraries

* ***NOTE*** Be careful to **not install `python3-django` from rpm** as this would give you 1.9 and the code would break.

* See `capture-versions.sh`  and files named `VERSIONS*` that give more details of what was running on nominal deployments, and on the actual split between what was installed with `dnf` and what comes from `pip`

```
dnf -y install python3
dnf -y install nginx
dnf -y install uwsgi uwsgi-plugin-python3
```

```
pip3 install --upgrade pip setuptools
pip3 install --upgrade Django django-extensions
pip3 install jsonpickle
# for nbh-monitor
pip3 install aiohttp docker

# see VERSIONS for python libraries
```

#### note on fedora upgrades

If you upgrade to a more recent fedora, as always `dnf` will take care of the packages that it knows about, but **won't automatically install the `pip` dependencies, that need to be reinstalled manually**.

## SSL certificates

The application can in theory run under simply `http`, but for any real deployment you're going to run as an iframe-embedded site for a main site that runs https (like e.g. `fun-mooc.fr`). In such a case running `nbhosting` behind `http` just won't work, as the browser won't allow it.

The default config has it that the SSL certificate used by the main entry point (in our case `nbhosting.inria.fr`) be located in `/root/ssl-certificate/`, and more specifically

```
$ egrep 'server|ssl_cert' nbhosting/main/sitesettings.py
server_mode = "https"
server_name = "nbhosting.inria.fr"
ssl_certificate = "/root/ssl-certificate/bundle.crt"
ssl_certificate_key = "/root/ssl-certificate/nbhosting.inria.fr.key"
```

Make sure to take care of these settings and cryptographic material.

## install and update

We do not expose any packaging; instead overall the workflow is to

* create a git clone in `/root/nbhosting`
* create a config. file by copying the provided template and editing it
* run the `install.sh` script in here to install (or, update just the same)

### initial installation

```
cd /root
git clone https://github.com/parmentelat/nbhosting.git
cd /root/nbhosting/nbhosting/main
cp sitesettings.py.example sitesettings.py
```

* at that point, edit `sitesettings.py`, and then

```
cd /root/nbhosting
./install.sh
```

that will also start the services, you should be good to go


### admin (create super user)

Initialize the admin superuser; preferably user `profs` - this is what will allow to enter the admin web interface:

```
cd /root/nbhosting/nbhosting
python3 manage.py migrate
python3 manage.py createsuperuser
```


## update to a more recent version

```
cd /root/nbhosting
git pull
./install.sh
```

Make sure to see the reservation explained in `configuration.md`, about possible new variables introduced in `sitesettings.py.example` in the meanwhile.


## use

There's a single command `nbh` that's an entry point into all the features exposed to the CLI; see the list with

```
nbh --help
```

****

# Managing courses

## initialisation (step 1 : pull from git)

```
nbh course-init flotpython https://github.com/parmentelat/flotpython.git
```

* this creates a course (the git repo in fact)
* that fyi goes in `/nbhosting/courses-git/flotpython/`

## updates (step 2 : update from git)

```
nbh course-update-from-git flotpython
```


* for now this **needs to be done at least once**
* as it will create the actual course notebooks master area
* which fyi again goes in `/nbhosting/courses/flotpython`

## image (step 3 : build image for course)

#### option1 : piggyback

If you use an nbhosting instance that already hosts a course, say `flotpython3`, and you want to host course `flotbioinfo` with the same image as `flotpython3`, you can do this:

```
nbh course-settings -i flotpython3 flotbioinfo
```

and check that your setting is properly displayed on the course page for `flotbioinfo`.


#### option2 : your own image

```
nbh course-build-image flotpython
```

* this assumes a dockerfile has been created for that course; this can be either

  * in the course git repo, under `nbhosting/Dockerfile`
  * or in `nbhosting`'s git repo itself, under `images`/*coursename*`.Dockerfile`

## UI

You can trigger steps 2 (update from git) and 3 (rebuild image) from the web UI at the course page (the same that shows a list of known notebooks).

## settings (optional)

**WARNING** this aspect of the system is undergoing quite substantial changes **WARNING**

### what ?

There are a few settings available for a course; as of this writing:

* docker image name to use; the default is the coursename, so `flotpython` looks for image `flotpython`; however images are big and tedious to build, so you could want to share another course's image
* students that are considered *staff*; corresponding hashes will be ignored when building usage statistics

* list of static mappings; see below
* sectioning and tracks; see below

By experience, the first two settings seem to make more sense on a nbhosting
deployment basis; the dev and prod boxes will not necessarily align on these.
The last ones on the other hand seem to depend on the git repo structure only,
and so are defined from files in the course repo.

### how ?

##### image and staff

The 2 first settings are stored in text files, e.g.

* `/nbhosting/courses/flotpython/.staff`
* `/nbhosting/courses/flotpython/.image`

that can be edited directly, or be changed with `nbh course-settings`; run with `--help` for more details

##### static mappings
static mappings allow you to define symlinks that work from anywhere in the notebooks tree; for example, if you define the following 2 mappings

```
data -> data
rise.css -> media/rise.css
```

then in every student work dir (i.e. every directory that contains at least one student notebook), the platform will create symbolic links named `data` and `rise.css`, that point at **read-only** snapshots of `data` and `media/rise.css`, from the git repo toplevel.

The default static mappings are defined as
```
data -> data
media -> media
```

but can be redefined in each course git repo in `nbhosting/static-mappings`

##### tracks

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

Beware that some settings are used at **container-creation** time; meaning that if a student has come at least once, her container exists and the course settings will be mostly ignored.

Same goes of course if a change is made to the course image (like, adding a python library).

This being said, a stopped container can be safely removed manually, causing it
to be re-created the next time a student shows up. But tearing down thousands of
containers can be time-consuming and create a big load on the box. To alleviate
for that, the monitor is instructed to remove containers that have not been used
in a fixed amount of time - typically a couple weeks. It also removes containers
that rely on an older version if the image.


****

# Ops

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

* `/nbhosting/logs/nbhosting.log`
* `/nbhosting/logs/monitor.log`
* `/nbhosting/logs/nginx-{error,access}.log`
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
* it is also possible to open any of the notebooks: go to the `notebooks` page for a given course (i.e. not the `stats` page); clicking any of the notebooks will open it as if opened by a student whose name is `anonymous`.
* this is a convenient way to check the course is up and running - in particular, make sure you have built the image for that course !

# comfort

Some additions of mine to feel a little more at home:

```
cd

dnf -y install git emacs-nox curl

git clone git://diana.pl.sophia.inria.fr/diana.git
diana/bash/install.sh -b 5 systemd git gitprompt
echo "source /root/nbhosting/zz-devel/logaliases" >> .bash-private.ish
```
