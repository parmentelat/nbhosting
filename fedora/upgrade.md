# Upgrading the underlying fedora

Here's how we manage this chore

## 2 boxes

We actually have 2 boxes running nbhosting, one of them being used for validating development changes. So in theory we have this mapping

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | production  | f27            |
| `thermals.inria.fr` | development | f27            |


The way a given box is attached to either of the 2 functions (production or development) is through its IP addresses, which in turns are managed as `systemd` services:

```
for service in nbhosting-addr nbhosting-dev-addr; do
    systemctl is-active $service
done
```

which btw is included in the following convenience alias:

```
source ~/nbhosting/zz-devel/upgradealiases
upgrade-status
```




## convenience

There are currently 2 pieces that can come in handy, they need to be reconciled:

* file `zz-devel/upgradealiases` for a few convenience tools that can ease the various steps in this workflow. In particular

| command                   |  purpose  |
|---------------------------|-----------|
| `upgrade-status`          | show which services are running and enabled |
| `upgrade-push-user-data`  | rsync user data prior to handover; as the name suggests, |
|                           | always **run from the current production box** |
| `upgrade-sizes`           | show sizes of data parts under `/nbhosting`  |


* see also file `zz-devel/upgrade-swap.sh` that has older code (used to upgrade from f25 to f27 apparently) and that should be useful too


## workflow

Before moving to a newer fedora, (or a newer django for that matter) it is of
course necessary to validate code. So the overall workflow is all about swapping the 2 boxes, like this:


### starting point

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | production  | f27            |
| `thermals.inria.fr` | development | f27            |

### upgrade dev box

Using `dnf system-upgrade`
<br/>
Note that packages installed with pip need to be manually reinstalled if the python3 version has increased.

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | production  | f27            |
| `thermals.inria.fr` | development | f29            |

then create a devel branch e.g. `f29` and get that to work on fedora29.

### redirect production traffic

at that point, after having tested as thoroughly as possible, we can:

* rsync user data from production to devel box (see `upgrade-push-user-data` below)
* redirect the production traffic to the devel box
* and temporarily drop the devel function (no box has the function, or the usual production box takes over)

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | none        | f27            |
| `thermals.inria.fr` | production  | f29            |

### upgrade the usual production box

now that thurst is idle it can be upgraded to f29

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | none        | f29            |
| `thermals.inria.fr` | production  | f29            |

### switch back

we can now

* sync user data back from the usual-dev box to the usual-prod box - using `upgrade-push-user-data` the other way around
* switch back production traffic to the usual prod box

| box                 | function    | fedora release |
|---------------------|-------------|----------------|
| `thurst.inria.fr`   | production  | f29            |
| `thermals.inria.fr` | none        | f29            |

### epilogue

At that point:
* the usual devel box can be reconfigured to work as a devel box
* to this end, double check `upgrade-status` on both boxes
* also, in `/nbhosting` we do the following renamings:
  * `mv students students.prod`
  * `mv raw raw.prod`

This is optional, it's a way to keep a backup, and to hopefully minimize the
amount of time needed next time.

## pitfalls

### swapping

When swapping a box from, say, devel to production: there currently is a need to

* manually manage (start/stop/enable) the IP addresses in use through related systemd services named in `nbhosting*addr.service`
* manually edit `django/nbh_main/sitesettings.py` to select the 3 lines that describe `server_name` and related SSL certificate
* re-run `install.sh`


### images

The way we build our images - based on the latest scipy stack image - means that we seldom have the exact same images on both boxes; which is a cool way to check for the latest image at the same time as we upgrade.

### btrfs volumes

Once a box *loses* its development function, a lot of btrfs volumes are left
over that may need to be cleaned up; removing all containers and images
is one way to do that, it might take some time though.
