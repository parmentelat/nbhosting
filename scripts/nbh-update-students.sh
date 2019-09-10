#!/bin/bash

function usage() {
    echo "Usage $0 [-p] [-s] course"
    echo "  performs a git pull on that course"
    echo "  then picks corresponding hash"
    echo "  and checks all the students spaces in students/*.*"
    echo "options"
    echo " -p: actually pulls from the students spaces"
    echo " -s: silent mode; students that are OK are not reported"
    exit 1
}

function current_hash() {
    git log -1 --pretty='%h'
}
 
# default is to just be watching
pull_mode=""
silent_mode=""
while getopts "ps" option; do
    case $option in
            p) pull_mode="true" ;;
            s) silent_mode="true" ;;
	    ?) usage ;;
    esac
done
shift $((OPTIND-1))
# reset OPTIND for subsequent calls to getopts
OPTIND=1
    
course=$1; shift

[ -n "$course" ] || usage
[[ -n "$@" ]] && usage

echo "pulling from git for course $course"
if [ -z "$silent_mode" ]; then
    nbh-manage course-pull-from-git $course 
else
    nbh-manage course-pull-from-git $course >& /dev/null
fi

cd /nbhosting/current/courses-git/$course
expected_hash=$(current_hash)
echo "expected hash extracted from $(pwd) as $expected_hash"


for student_home in /nbhosting/current/students/*.*; do
    student=$(basename $student_home)
    student_course=$student_home/$course
    if [ ! -d $student_home/$course ]; then
#	echo ==== $student has no working space for course $course
	continue
    fi
    cd $student_course
    student_hash=$(current_hash)
    if [ $student_hash == "$expected_hash" ]; then
        [ -z "$silent_mode" ] && echo == $student OK
    else
	if [ -z "$pull_mode" ]; then
	    echo XX $student is on $student_hash
	else
	    sudo -u $student git pull
	    new_hash=$(current_hash)
	    if [ "$new_hash" == "$expected_hash" ]; then
		[ -z "$silent_mode" ] && echo "++ $student pulled OK"
	    else
		echo "-- $student still behind on $new_hash"
	    fi
	fi
    fi
done
