# upgrade to Docker-CE

as per https://docs.docker.com/install/linux/docker-ce/fedora/#install-using-the-repository

## prepare

```
dnf -y install dnf-plugins-core
dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

systemctl stop docker
systemctl disable docker
```


*********
## uninstall

can't just install docker-ce, b/c of conflicts, let's uninstall

`rpm -qa | grep docker`  gives us

```
docker-rhel-push-plugin-1.13.1-65.git1185cfd.fc29.x86_64
docker-common-1.13.1-65.git1185cfd.fc29.x86_64
docker-1.13.1-65.git1185cfd.fc29.x86_64`
```

rpm -q --verify exhibits:

* ` docker`
  * `/etc/sysconfig/docker-storage-setup` which has only comments
* ` docker-common`
  * `/etc/sysconfig/docker` - for using btrfs

both backed up in .old-docker

```
rpm -e docker docker-common docker-rhel-push-plugin
```

## install CE

    dnf install docker-ce docker-ce-cli containerd.io

        Installed:
            containerd.io-1.2.4-3.1.fc29.x86_64
            docker-ce-3:18.09.3-3.fc29.x86_64
            docker-ce-cli-1:18.09.3-3.fc29.x86_64

    systemctl enable docker
    systemctl start docker
