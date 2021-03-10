#
# this file is a shell script template - do not edit !!
#
# purpose here is to trigger a course build in a podman container
# to that end, the regular course image is used, but a few additional
# steps are required:
# * preparation : clone the git repo uder /home/jovyan/work
# * execution: of the {script} phase as defined in nbhosting.yaml
# * croping: extract the result (as defined in result_folder)

here=$(dirname $0)

NBHROOT="{{NBHROOT}}"
coursename="{{coursename}}"
buildname="{{buildname}}"
githash="{{githash}}"
directory="{{directory}}"
result_folder="{{result_folder}}"
entry_point="{{entry_point}}"

host_repo="${NBHROOT}/courses-git/${coursename}"

# inspired by
# https://stackoverflow.com/questions/30488698/how-to-make-a-bash-function-return-1-on-any-error
user_code_in_subshell() (
set -e
cd {{directory}}
pwd
{{script}}
)

function clone_build_rsync() {
  id
  cd /home/jovyan/work
  git clone ${host_repo} .
  # set -e
  user_code_in_subshell
  if [ $? == 0 ]; then
    echo "build OK - installing"
    ls -ld $directory/$result_folder/ /home/jovyan/building/
    rsync -ai $directory/$result_folder/ /home/jovyan/building/
    exit 0
  else
    echo "build KO"
    exit 1
  fi
}

set -x
# clone_build_rsync 2>&1 > $here/.clone-build-rsync.log
clone_build_rsync
