#!/bin/bash
#
# this is a replacement for start.sh from base jupyter images
#
# our use case is:
# * a uid gets created in the host - with a loginname derived from uid
# * we want this user to run jupyter notebooks, in /home/jovyan
# * this dir is bind-mounted on the host filesystem
# * and then we want the host files to be tagged with this uid
#
# short of using user namespaces that neither docker nor systemd-nspawn
# seems to expose for that sort of usage, the angle here is to
# * take the 2 first arguments as dir and uid
#   the rest being the command to run
# * create the login/uid in the guest on a need-by-need basis
# * and then su to execute the command as that uid
# * no home-dir gets created, this is because the workdir is expected
#   to have been created and bind-mounted already
# * this strategy requires the container to be run as root
#   so we can mess with /etc/passwd
#
# in terms of chown:
# * typically /home/jovyan on the image is owned by uid 1000, of course
# * so there is a need to give this place to $uid
# * this is why we call start-in-dir-as-uid.sh with dir /home/jovyan
# * and then invoke jupyter notebook --NotebookApp.notebook_dir=/home/jovyan/work
# * this way the whole pseudo-home dir is fully writable by $uid and this is
#   needed when jupyter looks for its config and tries to do things like migration
#   and similar


USAGE="Usage: $0 dir uid command .. to .. run"
REQUIRE="Usage: $0 needs to be run as root"

dir=$1; shift
uid=$1; shift

[ -n "$1" ] || { printf $USAGE; exit 1; }

[ "$UID" -eq 0 ] || { printf $REQUIRE ; exit 1; }

# create uid if missing
# do not create homedir; this is because 
if getent passwd $uid; then
    # this uid already exists, let's figure what the login is
    login=$(getent passwd $uid | cut -d: -f1)
else
    login="uid$uid"
    useradd --uid $uid --no-create-home --shell /bin/bash $login
fi

# go to the place 
[ -d $dir ] || { printf "$0: no such directory $dir"; exit 1; }
cd $dir
# doing chown -R is overkill, and in fact a substantial fraction
# of the contents is bind-mounted anyway
# so instead we spot the files that are on the same filesystem
find . -mount | xargs chown $uid

##########
# use runuser, that will pass the environment as-is
# only need to tweak HOME just in case
##########
echo $0 exec-ing "$@" as uid "$uid" in $(pwd)

exec runuser --user $login -- env HOME=/home/jovyan "$@"
