#!/bin/bash


PULL_MODE=""
SILENT_MODE=""
FIND_MODE=""


# print current commit's hahs on stdout
function current-hash() {
    git log -1 --pretty='%h'
}
 

function update-course() {
    course=$1; shift

    echo "========== git pull for $course"
    if [ -z "$SILENT_MODE" ]; then
        nbh-manage course-pull-from-git $course 
    else
        nbh-manage course-pull-from-git $course >& /dev/null
    fi

    cd /nbhosting/current/courses-git/$course
    expected_hash=$(current-hash)
    echo "expected hash extracted from $(pwd) as $expected_hash"


    for student_home in /nbhosting/current/students/*.*; do
        student=$(basename $student_home)
        student_course=$student_home/$course
        if [ ! -d $student_home/$course ]; then
#	echo ==== $student has no working space for course $course
	    continue
        fi
        cd $student_course
        student_hash=$(current-hash)
        if [ $student_hash == "$expected_hash" ]; then
            [ -z "$SILENT_MODE" ] && echo == $student OK
        else
	    if [ -z "$PULL_MODE" ]; then
	        echo XX $student is on $student_hash
	    else
	        sudo -u $student git pull
	        new_hash=$(current-hash)
	        if [ "$new_hash" == "$expected_hash" ]; then
		    [ -z "$SILENT_MODE" ] && echo "++ $student pulled OK"
	        else
		    echo "-- $student still behind on $new_hash"
	        fi
	    fi
        fi
    done
}


function usage() {
    echo "Usage $0 [-p] [-s] [-f] course"
    echo "  performs a git pull on that course"
    echo "  then picks corresponding hash"
    echo "  and checks all the students spaces in students/*.*"
    echo "options"
    echo " -p: actually pulls from the students spaces"
    echo " -s: silent mode; students that are OK are not reported"
    echo " -f: courses are found by pattern using nbh-manage courses-list"
    exit 1
}


function main() {

    [[ -n "$@" ]] || usage

    # default is to just be watching
    while getopts "fps" option; do
        case $option in
            p) PULL_MODE="true" ;;
            s) SILENT_MODE="true" ;;
            f) FIND_MODE="true" ;;
	    ?) usage ;;
        esac
    done
    shift $((OPTIND-1))
    # reset OPTIND for subsequent calls to getopts
    OPTIND=1

    [[ -z "$@" ]] && usage
    if [ -n "$FIND_MODE" ]; then
        courses=$(nbh-manage courses-list "$@")
    else
        courses="$@"
    fi
    for course in $courses; do
        update-course $course
    done
}

main "$@"    

