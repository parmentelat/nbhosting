# Intro

* This document is about setting up `nbhosting` from scratch, i.e. fedora install.

# SSL certificates

* ***Don't forget*** to back up SSL certificate and especially ***the private key***

# Reinstallations

## iter 3 : exhibiting a mixed setup

* Overall performance with `btrfs` are reasonable, although not outstanding
* More benchmarks would be needed in order to compare the various options
* Have heard of the `overlay2` docker driver on the IRC channel and all over the place
* except that, lucky me, this won't work on btrfs
* so in order to avoid having to reinstall all the time
* I create 3 partitions so I can try more combinations

```
[root@thermals ssl-certificate]# df -h | grep /homefs
/dev/sda3       326G   33M  326G   1% /homefs/xfs
/dev/sda7       359G   17M  357G   1% /homefs/btrfs
/dev/sda2       321G   69M  305G   1% /homefs/ext4
```

## iter 2 : using btrfs

* It is **crucial to use `btrfs`** and ***NOT LVM*** - at any rate!
* I am repeating the process on Jan. 26 2017
* mostly because the first setup was running **on top of LVM** which induced this message by docker

```
Jan 26 11:34:40 <snip> level=warning msg="devmapper: Usage of loopback devices is strongly discouraged for production use. Please use `--storage-opt dm.thinpooldev`  or use `man docker` to refer ....
```

* as well as, most importanty, numerous errors while trying to rm a docker instance, like 

```
Driver devicemapper failed to remove root filesystem 57fd75dc922b806cfff034b571388066da807e0712f80014e799331217377828: Device is Busy
```

* we don't need LVM indeed since we already have RAID underneath, so ext4 sounds about right

## iter 1 - LVM
* jan 9 2017
* fedora 25 - server
* not paid too much attention, ended up with the standard LVM setup
* turned off sshd password auth in `/etc/ssh/sshd_config`
* turn off f... selinux: 
  * the `SELINUX=disabled` option is configured in `/etc/selinux/config`
  * [see also this page](http://stackoverflow.com/questions/26334526/nginx-cant-access-a-uwsgi-unix-socket-on-centos-7) in particular the location for the interesting log `/var/log/audit/audit.log`


# config

## iptables

see `fedora/etc/sysconfig/iptables`

## selinux

see `fedora/etc/selinux/config`

## packages

```
dnf -y install git emacs-nox
dnf -y install python3 python3-django
dnf -y install docker
dnf -y install nginx
dnf -y install -y uwsgi uwsgi-plugin-python3
dnf -y install -y curl

pip3 install --upgrade pip setuptools
pip3 install --upgrade Django
pip3 install --upgrade docker
```

```
[root@thermals sysconfig]# rpm -q docker nginx uwsgi
docker-1.12.6-5.git037a2f5.fc25.x86_64
nginx-1.10.2-1.fc25.x86_64
uwsgi-2.0.14-3.fc25.x86_64

[root@thermals ~]# python3 --version
Python 3.5.2

[root@thermals ~]# python3 -c 'import django; print(django.__version__)'
1.10.5

```

## services

### nbhosting services

```
systemctl start docker
systemctl enable docker
docker pull jupyter/scipy-notebook
docker pull jupyter/base-notebook

systemctl start nginx
systemctl enable nginx
```

### iptables vs firewalld

```
dnf install -y iptables-services
systemctl mask firewalld.service
systemctl enable iptables.service
```

of course **reboot as needed** (esp. regarding selinux)

****
# App install

## Initial install

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


## Updates

```
cd /root/nbhosting
git pull
./install.sh
```

****

# Install courses

## Initialisation (item 1 : pull from git)

* Create a course (the git repo in fact) in `/nbhosting/courses-git/flotbioinfo/`

```
nbh-init-course /nbhosting flotbioinfo https://github.com/parmentelat/flotbioinfo.git
```

## Updates (item 2 : update notebook master area from git)

* For now this **needs to be done at least one**, as it will create the actual course notebooks master area in `/nbhosting/courses/flotbioinfo`

```
nbh-update-course /nbhosting flotbioinfo
```

## Image (item 3 : build image for course)

* This assumes a dockerfile has been created for that course

```
cd /root/nbhosting/docker-images
make flotbioinfo
```

****

# comfort

```
cd
git clone git://diana.pl.sophia.inria.fr/diana.git
diana/bash/install.sh -b 5 systemd
echo 'alias nbha=nbh-admin' >> .bash-private.ish
echo source /root/nbhosting/zz-devel/logaliases >> .bash-private.ish
```
