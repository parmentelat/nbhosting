#!/bin/bash

function usage() {
    echo "[-u] Usage $0 course"
    echo "the expected hash for all students spaces"
    echo "is extracted from the course-git area"
    exit 1
}

function current_hash() {
    git log -1 --pretty='%h'
}
 
# default is to just be watching
pull_mode=""
while getopts "p" option; do
    case $option in
            p) pull_mode="true" ;;
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
nbh-manage course-pull-from-git $course

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
	echo == $student OK
    else
	if [ -z "$pull_mode" ]; then
	    echo XX $student is on $student_hash
	else
	    sudo -u $student git pull
	    new_hash=$(current_hash)
	    if [ "$new_hash" == "$expected_hash" ]; then
		echo "++ $student pulled OK"
	    else
		echo "-- $student still behind on $new_hash"
	    fi
	fi
    fi
done
