# Intro

* This document is about setting up `nbhosting` from scratch, i.e. fedora install.

# SSL certificates

* ***Don't forget*** to back up SSL certificate and especially ***the private key***

# installation

## Disk partitioning

### production 

`nbhosting` essentially uses 2 distinct areas

* `/nbhosting` to store valuable data, that can sit on any filesystem of your choice, that contains namely
  * the students notebooks
  * the courses notebooks (from git)
  * logs, raw data for stats, ...

* `/btrfs` : an area for docker to deploy its images; there are many options here, but  I have made successful tests with `btrfs` (see `flavours-docker/etc-sysconfig-docker.btrfs`), so I assume that we have a reasonable space dedicated to this.

At first sight, on a 1Tb hdd, I would suggest to allocate about 50-50 to these 2 areas; in theory the copy-on-write scheme used by docker avoids the need for much space in `/btrfs/` but still, several tens of Mb per student for logs only is to be expected


### devel setup

in my devel setup the `btrfs` partition was `/homefs/btrfs` because I have been running with several partitions to play with the different docker schemes:

```
[root@thermals ssl-certificate]# df -h | grep /homefs
/dev/sda3       326G   33M  326G   1% /homefs/xfs
/dev/sda7       359G   17M  357G   1% /homefs/btrfs
/dev/sda2       321G   69M  305G   1% /homefs/ext4
```

# config

## iptables

see `fedora/etc/sysconfig/iptables`

## selinux

see `fedora/etc/selinux/config`

## services

### iptables vs firewalld

```
dnf install -y iptables-services
systemctl mask firewalld.service
systemctl enable iptables.service
```

of course **reboot as needed** (esp. regarding selinux)

# packages / dependencies

### IMPORTANT NOTES about python libraries

* ***NOTE*** Be careful to **not** install `python3-django` from rpm as this would give you 1.9 and the code would break.

* See `capture-versions.sh`  and files named `VERSIONS*` that give more details of what was running on nominal deployments, and on the actual split between what was installed with `dnf` and what comes from `pip`

```
dnf -y install git emacs-nox curl

dnf -y install python3 
dnf -y install -y uwsgi uwsgi-plugin-python3
pip3 install --upgrade pip setuptools
pip3 install --upgrade Django

# see VERSIONS for python libraries
```

****

# Comfort

Some additions of mine to feel a little more at home:

```
cd
git clone git://diana.pl.sophia.inria.fr/diana.git
diana/bash/install.sh -b 5 systemd
echo 'alias nbha=nbh-admin' >> .bash-private.ish
echo source /root/nbhosting/zz-devel/logaliases >> .bash-private.ish
```

****
# App install

## initial install

```
cd /root
git clone https://github.com/parmentelat/nbhosting.git
cd nbhosting
./install.sh
```

## admin (create super user)

Initialize the admin superuser :

```
cd /root/nbhosting/django
python3 manage.py migrate
python3 manage.py createsuperuser
```


## update to a more recent version

```
cd /root/nbhosting
git pull
./install.sh
```

**NOTE** I need to double-check this, but install.sh very probably restarts the docker service; which in turn, will restart **all containers**, so it's very intrusive.

I might have to provide an option to this less aggressively, but in devel mode that's how I do it.

****

# Install courses

```
nbh --help
```
## initialisation (item 1 : pull from git)

* Create a course (the git repo in fact) in `/nbhosting/courses-git/flotbioinfo/`

```
nbh init-course flotbioinfo https://github.com/parmentelat/flotbioinfo.git
```

## updates (item 2 : update notebook master area from git)

* For now this **needs to be done at least one**, as it will create the actual course notebooks master area in `/nbhosting/courses/flotbioinfo`

```
nbh update-course-from-git course flotbioinfo
```

## image (item 3 : build image for course)

* This assumes a dockerfile has been created for that course

```
cd /root/nbhosting/docker-images
make flotbioinfo
```

## settings (optional)

### what ?

There are a few settings available for a course; as of this writing:

* docker image name to use; the default is the coursename, so `flotbioinfo` looks for image `flotbioinfo`; however you could also create flotpython-session1 that uses image `flotpython`

* list of static dirs; the default here is `media` and `data` which are the conventions hard-wired in the previous notebook hosting system; when trying to deploy 'Data Science Handbook' it appeared that this should be configurable

### how ?

These settings are stored in e.g.

* `/nbhosting/courses/flotbioinfo/.statics`
* `/nbhosting/courses/flotbioinfo/.image`

that can be edited directly, or be changed with `nbh course-settings --help`

### when ?

The settings are used at **container-creation** time; meaning that if a student has come at least once, her container exists and the course settings will be mostly ignored.

Same goes of course if a chnge is made to the course image (like, adding a python library). 

This being said, a stopped container can be safely removed manually, causing it to be re-created the next time a student shows up. But tearing down thousands of containers can be time-consuming and create a big load on the box.


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
* `/var/log/nginx/{error,acces}.log`
* also each docker container can be probed for its logs
  * `docker logs flotbioinfo-x-theimpossibletorememberstudentid`

## visual stats

* https://nbhosting.inria.fr/nbh/ is the - very rough - front-end for the django app
* it targets only the admin of course, and the login/passwd for the admin user was created above (see `manage.py createsuperuser`)
* main page is `https://nbhosting.inria.fr/nbh/courses`; each course comes with its stats page; probably subject to changes, so you'd better see for yourself, but as of now:
  * number of registered students 
  * number of notebooks read
  * number of containers/kernels
  * disk space
  * cpu load
