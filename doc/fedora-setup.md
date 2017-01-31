# nbhosting setup

## SSL certificates

* Don't forget to back up SSL certificate and especially **the private key**

## Reinstall

### redeux : using btrfs

* It is **crucial to use `btrfs`** and **NOT** at any rate LVM
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

### initial attempt
* jan 9 2017
* fedora 25 - server
* turned off sshd password auth in `/etc/ssh/sshd_config`
* turn off f... selinux: 
  * the `SELINUX=disabled` option is configured in `/etc/selinux/config`
  * [see also this page](http://stackoverflow.com/questions/26334526/nginx-cant-access-a-uwsgi-unix-socket-on-centos-7) in particular the location for the interesting log `/var/log/audit/audit.log`


## config

### iptables

see `fedora/etc/sysconfig/iptables`

### selinux

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

## comfort

```
cd
git clone git://diana.pl.sophia.inria.fr/diana.git
diana/bash/install.sh -b 5 systemd
echo 'alias nbha=nbh-admin' >> .bash-private.ish
echo source /root/nbhosting/zz-devel/logaliases >> .bash-private.ish
```
