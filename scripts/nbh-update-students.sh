#!/bin/bash
shopt -s nullglob

COMMAND=$0

NBHROOT="/nbhosting/current"

PULL_MODE=""
RESET_MODE=""
QUIET_MODE=""
STUDENTS=""


# print current commit's hahs on stdout
function current-hash() {
    git log -1 --pretty='%h'
}
 
function die() {
    echo "$@" - aborting; exit 1
}

function update-course-for-students() {
    course=$1; shift
    students="$@"

    echo "========== git pull for $course"
    nbh-manage course-pull-from-git $course >& /dev/null
    
    cd /nbhosting/current/courses-git/$course
    expected_hash=$(current-hash)
    echo "expected hash extracted from $(pwd) as $expected_hash"


    for student in $students; do
        student_home=$NBHROOT/students/$student
        student_workspace=$student_home/$course
        [ -d $student_home/$course ] || continue
        cd $student_workspace
        student_hash=$(current-hash)
        if [ $student_hash == "$expected_hash" ]; then
            [ -z "$QUIET_MODE" ] && echo == $student OK
        else
	    if [ -z "$PULL_MODE" ]; then
	        echo XX $student is on $student_hash
	    else
            [ -n "$RESET_MODE" ] && git reset --hard
	        sudo -u $student git pull
	        new_hash=$(current-hash)
	        if [ "$new_hash" == "$expected_hash" ]; then
		    [ -z "$QUIET_MODE" ] && echo "++ $student pulled OK"
	        else
		    echo "-- $student still behind on $new_hash"
	        fi
	    fi
        fi
    done
}


function usage() {
    echo "Usage $COMMAND [-p] [-q] [-s student-pattern] course-patterns"
    echo "  performs a git pull on that course"
    echo "  then picks corresponding hash"
    echo "  and checks all the students spaces in students/*.*"
    echo "options"
    echo " -q: quiet mode; students that are OK are not reported"
    echo " -p: actually pulls from the students spaces"
    echo " -r: performs git reset --hard before pulling (thus requires -p)"
    echo " -s: specify students by pattern - cumulative"
    echo ""
    echo "Example"
    echo " $COMMAND -p python bioinfo"
    echo " $COMMAND -q mines"
    echo " $COMMAND -rp -s thierry.parmentelat -s cyril.joly python-primer" 
    exit 1
}


function main() {

    [[ -n "$@" ]] || usage

    cd $NBHROOT/students
    # default is to just be watching
    while getopts "pqrs:" option; do
        case $option in
            p) PULL_MODE="true" ;;
            q) QUIET_MODE="true" ;;
            r) RESET_MODE="true" ;;
            s) STUDENTS="$STUDENTS $(echo $OPTARG)" ;;
	    ?) usage ;;
        esac
    done
    shift $((OPTIND-1))
    # reset OPTIND for subsequent calls to getopts
    OPTIND=1

    [[ -z "$@" ]] && usage
    courses=$(nbh-manage courses-list "$@")
    if [ -z "$STUDENTS" ]; then
        STUDENTS=$(echo *.*)
    fi
    [ -z "$STUDENTS" ] && die no student found
    STUDENTS=$(ls -d $STUDENTS | sort -u)
    [ -z "$STUDENTS" ] && die no student found
    for course in $courses; do
        update-course-for-students $course $STUDENTS
    done
}

main "$@"    

