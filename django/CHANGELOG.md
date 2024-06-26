# ChangeLog

## 0.59.0 2024 Jun 24

* for fedora40 - and possibly due to git-2.45
  change the way we clone to create the student repos

## 0.58.0 2024 May 2

* the format for specifying tracks has slightly changed
  it is now possible to specify a file stem (without extension)
* this is to accomodate the new script `jb-to-nbh-toc.py`
  that helps maintain the tracks part of `nbhosting.yaml` 
  from a jupyter-book `_toc.yml`

## 0.57.1 2024 Apr 18

* bypass nginx buffering on the streaming http response
  so we do get the process outputs on the fly this time

## 0.57.0 2024 Apr 18

* increase timeouts for nginx and gunicorn to 500 s
  to allow long-running processes like build-image to go through
* a first stab at displaying processes outputs on the fly
  used for course-management functions
  not yet perfect, likely requires going aync on the django side

## 0.56.1 2024 Feb 4

* pull reference images from quay.io instead of docker.io
  as the latter are no longer maintained as per this statement
  > Images hosted on Docker Hub are no longer updated. Please, use quay.io

  https://quay.io/repository/jupyter/scipy-notebook
* 0.56.0 was broken, do not use, because of the entrypoint
  set in the upstream images that was not compatible with our

## 0.55.2 2024 Jan 16

* miscell tweaks about using grep -E

## 0.55.1 2023 Dec 10

* suitable for fedora 39
  was just missing an explicit dep. to 'rich' in setup.py
  which should have come with podman-py

## 0.55.0 2023 Dec 10

* the content of the stock images is reviewed for being to use nb7
  * fewer implicit dependencies
* see .nbhosting/Dockerfile in flotpython/course
  for instructions on how to adapt your Dockerfile
  if moving over from nbclassic
* other courses may need to add a few pip installs in their Dockerfile

## 0.54.3 2023 Nov 1

* publish on pypi

## 0.54.2 2023 Oct 19

* bugfix in /usr/bin/nbh, was missing a dash in a call to --course-update-jupyter
* I wonder how this can have gone unnoticed for so long
* worth being noted, happened after an upgrade to f38

## 0.54.1 2023 Oct 11

* redthedocs_url -> external_url

## 0.54.0 2023 Oct 11

builds no longer require a script

* make room for dummy redirection sites like
  e.g. ue22-p22-networking that comes with only
  the URLs to Basile's website
* build with no script won't trigger
* the auditor-courses and public-group-courses pages
  now display properly builds when they have either
  a successful script, or an external url
* at this point the external urls are still called
  readthedocs_url, but this will change soon

## 0.53.1 2023 Sep 24

* build instances can define a `readthedocs_url` field in their yaml config to
  specify an alternate URL where to find that build

## 0.52.6 2023 Aug 29

* new command `nbh-manage course-image-details` to display the versions
  inside a course image

## 0.52.5 2023 Aug 28

* nbh-manage build-images accepts a -t option to specify a tag
* since this is intended for frozen images,
  running build-images with no tag just rebuilds the `latest` tag
* this is intended for "frozen" jupyter images, like the ones
  that we tag 'nb6' that we will keep on using for MOOCs at least
  for the time being, until a more elaborate jupyterlab-nbhosting
  extension is available

## 0.52.4 2023 Aug 26

* add support for builds-filter in courses yaml config
* revisit course jupyter customization
  * the nbhosting repo comes with decent defaults in the jupyter/ folder
    * custom.css and custom.js have moved under jupyter/custom/
    * predefined labconfig/ and nbconfig/
  * these are automatically inherited by courses as they provide
    reasonable defaults
  * but can be overridden in the .nbhosting/jupyter folder if needed
    (using the same layout)
  * except for jupyter_notebook_config.py :
    the nbhosting version takes precedence as it contains security-oriented settings

  * in the mix, we change the layout of
    nbhroot/jupyter/ to accomodate for the above

## 0.52.3 2023 Jun 28

* tweak presentation of nbhosting:title as version is no longer used
* course names can contain digits - not as the first char though
* wildcard rule that redirects all the unknown traffic to /welcome
  is removed; only / goes to /welcome, and let others trigger 404

## 0.52.2 2023 Jun 21

* in preparation for jlab4 and nb7, the server is started as
  `jupyter lab` and no longer `jupyter notebook`
* the classic notebook takes all the horizontal space

## 0.52.1 2023 Jun 12

* spawns the notebook server as `jupyter lab` and no longer `jupyter notebook`
* this does not change anything from a user perspective, as the URL used to open
  a notebook is defined in the notebook-url-format
* but it does help to open jlab pages, that otherwise end up on a password page
  (go figure...)

## 0.52.0 2023 Jun 9

* new command `find-old-students.py` spots students that had no recent activity
* `nbh-to-jb-toc.py`, the tool that helps maintain a jupyter-book `_toc.yml` from
  `nbhosting.yaml`, has a new `-p` option that can do replacements
  such as removing the `notebooks/` part
* remove the `nb6` banner that warns about forthcoming `nb7` breakage of extensions
* `nbh-manage pull-student` has 2 new options to do a hard reset in the student's space

## 0.51.2 2022 Nov 27

* align code with using podman-py release 4.3.0 from pypi
* make sure to configure git safe-directory for git>=2.35
* new script nbh-to-jb-toc.py as an attempt to automate
  consistency between in nbhosting toc and jupyter-book toc

## 0.51.1 2022 Sep 9

* fix missing version in public/ page
* mass-register to use csv format for inputs instead of our own .input one

## 0.51.0 2022 Sep 6

* new url `/public/<group-name>` allows to navigate the
  available builds for all courses attached to that group
  (and that have at least one build)
* mass-register with -l shows the input lines as they are read
  to help pinpoint input issues

## 0.50.2 2022 Aug 16

* tweaks to improve git operations, both from the host (when running nbh-pull-student)
  and from the student's container (when using jupyterlab-git, or the terminal)
* at this point we still experience an issue when displaying differences
  <https://github.com/jupyterlab/jupyterlab-git/issues/1158>

## 0.50.1 2022 Aug 16

* run apt-get install with the -y flag when building core images
  needed with the latest jupyter images as exposed on dockerhub
  as otherwise rsync does not make it on the images, and builds
  fail for that reason

## 0.50.0 2022 Aug 16

* robustified nbh-pull-student
* reviewed the 'other views' area for smoother interactions,
  * with the tooltips placed properly
  * can reload a @classic or @jlab page
  * browsing a droparea now relies on jlab
  * jlab can open jupytext notebooks with a usual click
    this requires the course to customize labconfig/default_setting_overrides.json

## 0.49.0 2022 May 15

* minimal support for nb7
  * course can define in its general section
    `notebook-url-format: /edit/{notebook}?factory=Jupytext%20Notebook`
  * at this point this requires the Dockerfile to have pinned at least
    `RUN pip install "notebook>=7.0.0a1" "jupyterlab>=4.0.0a20"`
  * in this release the notebook menus are as-is, and in particular our 3 additions
    (reset-to-origin; share-as-static; show-student-id) are not available in nb7
* tracks-filter setting is now superseded (instead of extended as it was before)
* nbstripout added as a requirement; it's needed in pull-student

## 0.48.0 2022 May 13

* local-defined yaml file is now merged on top of course-provided file
* one can also define a new 'tracks-filter' field as a list of the track ids
  for the course
* this way one can create local tracks, and if needed ignore some course-provided tracks
* nbh-show-locals is a command that outlines the local/ area contents

## 0.47.2 2022 Mar 28

* add an entry in the File menu to display the student's id

## 0.47.1 2021 Dec 20

* remove dependency to uwsgi (close #150)
* replace runtime with gunicorn
* replace uwsgi shared memory (see v0.34 below)
  with a local redis service
* 0.47.0 had a broken install script

## 0.46.3 2021 Dec 19

* no functional change, and still uwsgi-based
* change repo layout to accomodate for gunicorn-based deployments

## 0.46.2 2021 Dec 19

* skip pulling archived courses
* upgrade-swap disk-status

## 0.46.1 2021 Sep 14

* bugfix, using .nbhosting/ instead of nbhosting/
  was not properly handled wrt nbconfig/notebook.json

## 0.46.0 2021 Sep 10

* courses can choose to store nbhosting-related configs
  in either nbhosting/ (like before) or .nbhosting (new)
  so that this folder does not encumber student space

## 0.45.0 2021 Sep 7

* mass-register enforce a maximum username lenghth of 31 (#119)
* autobuild now only affect pulls made by autopull (#148)
* fix UI bug, autobuild always False in course editing view (#147)

## 0.44.1 2021 Sep 2

* show available builds in main courses page

## 0.43.4 2021 Aug 2

* mass-register is able to export users in json format for the benefit of other django apps
* jupytext[myst] dep is now simply jupytext

## 0.43.3 2021 Jun 10

* staffs definition can refer to groups using the @group notation

## 0.43.2 2021 Jun 10

* the @classic and @jlab URLs accept a path

## 0.43.1 2021 Jun 9

* preliminary droparea feature
  * define a droparea by creating a subdir named `NBHROOT/droparea/<coursename>/<droparea>`
  * staff members can use the `/teacher/droparea/<coursename>/<droparea>/` url to manage
    (corresponding entries are created in the other view area for staff members)
  * i.e. upload/remove files in the droparea
  * and deploy them to the students that have registered for that course
  * students have an entry point in the 'other views' area
* 0.43.0 is broken

## 0.42.0 2021 Jun 7

* no longer rely on our patchy podman-py, use upstream release 3.x

## 0.41.4 2021 Jun 3

* CLI listing tools improved
  * more adapted to being used in shell scripts
  * harmonized behavior of the additive -l option
* nbh-manage user-list: new command
* nbh-manage course-list:
  * regular version can show groups and # of users
  * new -g and -u options to dig into groups and users
  * new -i option to show warnings for unknown images

## 0.41.3 2021 Apr 29

* remove persistent warning issued by Django3.2 about default primary keys

## 0.41.2 2021 Apr 28

* allow jupyterlab-git extension install to fail
* revisited the 'other views' area

## 0.41.1 2021 Mar 17

* bugfix monitor was failing to cleanup lingering containers #145

## 0.41.0 2021 Mar 17

* add autobuild in the course model
* pulling a course that has autobuild set triggers all builds on that course

## 0.40.2 2021 Mar 15

* nbh-manage course-pull no longer does git pull but fetch + reset --hard  
  the current branch is used as-is, note that the remote is expected to be called `origin` #138

## 0.40.1 2021 Mar 15

* nbh-manage course-run-build --force #141
* builds have more fields: id + name + description #142

## 0.40.0 2021 Mar 14

* the list of builds is used to create additional navigation buttons in the 'other views'
  area #140  

## 0.39.0 2021 Mar 10

* revised definition of the build object, new field directory,
  deprecate mount_as, defaults adapted to a sphinx build

## 0.38.2 2021 Mar 10

* minor bugfixes in yaml-config

## 0.38.1 2021 Mar 9

* nbh-manage course-tracks --yaml
  is a helper tool to produce a yaml extract as a replacement to tracks.py

## 0.38.0 2021 Mar 9

* the `static-mappings` and `tracks.py` configurations can now be done
  through a unified yaml file expected to be in `nbhosting/nbhosting.yaml`
* if the yaml file is found, the other 2 old-style config files
  (again `traks.py` and `static-mappings`) are ignored
* courses can also define builds, like for instance
  to recompute a static html version using jupyter-book
* nbh-manage course-run-build allows to trigger those builds
* this is not yet connected to course-pull #139
* nor does the UI have any button to reach those builds yet #140

## 0.37.0 2021 Feb 8

* use nbhosting metadata if present instead of notebookname #137
* that is to say `nbhosting.title` and `nbhosting.version` have precedence over toplevel
  `notebookname` and `version` resp.

## 0.36.3 2020 Dec 14

* follow-up on #135, all error pages return a 400 HTTP status

## 0.36.2 2020 Dec 14

* follow-up on #136, sort courses based on name

## 0.36.1 2020 Dec 13

* for #135: support a URL in /containerKill/course/student/

## 0.36.0 2020 Dec 12

* close #136
  * all 4 course management commands (list, pull, build-image, tracks)
    use a unified selection mechanism
  * beware that the --all option is no longer needed not supported
    just call the command with no parameter to get same effect

## 0.35.1 2020 Dec 12

* close #132 - new management command course-group
* close #118 - improved course-list

## 0.35.0 2020 Nov 23

* close #129
  * U and D keyboard shortcuts always allow to move cells up and down
  * plus, the native up and down buttons can be displayed
    with the show_up_down_buttons (see below)
* close #130
  * metadata can be nested in the 'nhosting' toplevel category as

    ```yaml
    nbhosting:
      title:
      version:
      show_up_down_buttons: yes
    ```

    missing version is OK, unrelevant versions are no longer displayed
* close #131
  * nbdime extension area disabled

## 0.34.0 2020 Nov 21

* simultaneous requests
  * this is to address a concern experienced by magistere, who has pages
    containing several iframes to the same course
  * the nbh script needs to determine if the container is already running
    and so if several attempts are made at the same time, they all believe
    the container is down and all try to spawn it, but only one can succeed
  * so in this version, an exclusive lock mechanism - using uwsgi cache to
    share this global info between uwsgi worker processes - prevents
    simultaneous attempts to spawn 2 notebooks from the same container

## 0.33.1 2020 Nov 11

* more compact output for nbh-pull-student (1 or 2 lines per student)
* miscell tweaks in the doc to adapt for fedora 33

## 0.32.9 2020 Oct 25

* fix #126

## 0.32.8 2020 Oct 13

* unpin notebook version (pinned in 0.32.1) as version 6.1.4
  has fixed the issue, that for the record was with narrow
  pages being further shrunken by half

## 0.32.7 2020 Oct 13

* notebooks_by_patterns no longer does a global sort
  just concatenate the (sorted) sequences issued by
  notebooks_by_pattern

## 0.32.6 2020 Oct 6

* new function notebooks_by_patterns (plural)
  that allows to pass several patterns in tracks.py

## 0.32.5 2020 Sep 18

* fix #123

## 0.32.4 2020 Sep 13

* fix #117

## 0.32.3 2020 Sep 11

* fix #116

## 0.32.2 2020 Sep 5

* fix #120, take more users into account when computing stats

## 0.32.1 2020 Sep 5

* emergency fix, pin notebook==6.0.3  
  <https://github.com/jupyter/notebook/issues/5687>

## 0.32.0 2020 Aug 3

* nbh-manage commands get renamed
  build-core-images -> build-image
  groups-list -> group-list
  courses-list -> course-list
  course-pull-from-git -> course-pull
  course-show-tracks -> course-tracks
* new command nbh-manage course-delete
* deprecation of $NBHROOT/logs
* review how tracks are displayed
  in particular a Track object now has an id field
  that is computed from name unless it is explicitly given
  to the constructor
* tracks with no notebook get sanitized

## 0.31.0 2020 Aug 3

* a course can be set as 'archived', so it won't show up in the standard courses index page
* allow a course to customize nbconfig/notebook.json in its nbhosting/ subdir
* core images come with jupytext[myst]
* use latest jupyterlab, with functional git extension
  to get this to work an additional mountpoint may be created in the container
* add some convenience scripts that were used to transfer
  the MOOC on fun-mooc.fr from .ipynb to .md

## 0.30.6 2020 Jun 22

* container memory limit configurable in sitesettings.py
* stats also gather available memory, as well as total containers and kernels
* hardened monitor
* bugfix: nbh-manage containers with selection pattern on courses

## 0.30.5 2020 Jun 19

* hard-wired memory limit on a container = 5g  
  test framework tweaked so we can provide our own test notebooks  
  new such test for memory exhaustion
* stats page has a new section on system memory used
* conmon process no longer in the systemd cgroup, runs in a cgroup of its own
* more robust monitor for podman
* smarter nbh-manage containers

## 0.30.4 2020 Jun 10

* use systemd setting to fix the containers being killed upon restart of django

## 0.30.3 2020 Jun 10

* modify install.sh to not restart the nbh-django service, this is too
  intrusive and messes with the containers
* new management command nbh-manage containers [-c] to display containers
  and kernels and last activity
* more robust course-create,
  rolls back DB insertion if git clone doesn't go through
* doc has a section on installing podman-py

## 0.30.2 2020 Jun 04

* podman-ready release, tested on f32 with cgroupv2
* comes with sysctl settings on the fs.inotify area that makes the system
  much more resistant to heavy load
* sets max. # of open files in ulimit and systemd service files while at it
* all ApiConnection instances are now volatile
* test summary show std. dev. instead of variance

## 0.30.1 2020 Jun 02

* beta-release for a podman-powered version to run on f32
  * to be assessed: heavy-duty tests have exhibited containers ending up
    in weird states, like `stopped` or even sometimes `configured`; current monitor
    has provisions to remove those, and logging them with a BLIP mark; hopefully
    this won't happen with actual loads
* more robust error handling when the course image cannot be found; which is helpful
  to troubleshoot misconfigured deployments
* error 502 should essentially be gone; when a user quickly selects a new notebook,
  because the container was already running we redirected right away and skipped waiting
  for the http port to be up; that was wrong
* slightly improved tests framework
  * nbhtests allows to set monitor idle time
  * summary.py can anayse an artefacts/ subdir and show interesting stats
  * nbhtests-log anf nbhtests-nohup are useful wrappers to capture LOG and run unattended
  * artefacts automatically renamed as per nbhtests options
  * slight changes in the testing logic; when several notebooks are passed to nbhtest,
    add an idle timer between successive hits

## 0.27.1 2020 Jun 02

* pull-student will abort merge if that failed
* maintenance release for the docker version
* new setting 'lingering' in monitor; kill any container older than that, no matter the activity
* install the django app using `pip install` instead of `setup.py install`
* reviewed install dependencies
* unified sitesettings template for production and devel boxes
* more robust install script wrt sudoers and iptables
* minor updates in fedora installation doc
* pin version of jupyterlab to be == 1 until our deps - mainly the git ext - support more recent releases
* minor improvements in upgrade-swap

## 0.27.0 2020 Mar 27

* fix for #111 and the SameSite cookie policy pushed in recent chromes
  hopefully temporary

## 0.26.0 2020 Jan 22

* **NEW mandatory SETTING**; you need to define `notebook_extensions` in `sitesettings.py`
* more jupytext-friendly; the extensions declared in that new setting
  are considered as possible notebooks, that can be opened directly
  **NOTE** that at this point there remains some places where the assumed value
  of `["ipynb", "py", "md"]` is hard-wired
* some provisions made for finer-grained logging of container warmup sequence
* bugfix #107
* still based on docker; an attempt to move to podman is [currently stalled because of an issue with the Python API](https://github.com/containers/python-podman/issues/72)

## 0.25.3 2019 Nov 20

* another corner case handled more gracefully, when a notebook is opened at a point
  where the container is being removed
* nicer and more informative error pages
* 0.25.2 is badly broken, DO NOT USE

## 0.25.1 2019 Nov 19

* global timeout raises to 30s; it's a lot, but it turns out it is necessary; I suspect
  some components in the image (jlab ?) may be in part responsible for slowing things down
* bugfix in monitor: it was causing a few mishaps when it killed containers that were not
  reachable because actually just taking off
* refactored edxfront view for more consistent rendering in case of failures
* various improvements in the tests area
* bugfix in install script

## 0.25.0 2019 Nov 18

* fix nbh shell script so that failing calls get logged properly
* more site-specific configuration options, issues ## 103 104 105 106
* minor cleanup in the log initialization code

## 0.24.5 2019 Nov 17

* attempted bugfix: prior code was not performing port allocation properly,
  and so when a busy port was picked we were getting the infamous 'failed-timeout'
  error message

## 0.24.4 2019 Nov 14

* fix the jupyter classic/lab buttons

## 0.24.3 2019 Nov 14

* increase timeout when spawning containers from 12 to 20s

## 0.24.2 2019 Nov 13

* 0.24 is good to go
* minor tweak to smooth migration: stopped containers, sequels of a pre-0.23 deployment,
  are killed before returning an error
* tests are operational again, running on a headless chromium

## 0.24.1 2019 Nov 8

* simplified container creation code now that containers are
  deemed oneshot, and destroyed after their idle time
* removed --unused option in monitor which is now meaningless

## 0.24.0 2019 Nov 7

* major rework of the overall routing scheme
* no longer relies on cookies to route properly !
* which in turn makes multi-course sessions a lot more reliable
* see issue #102 and commit 8faa38

## 0.23.2 2019 Nov 4

* cosmetic tweaks in the staff course view
  when showing members of the groups attached to a course

## 0.23.1 2019 Nov 4

* close #100: logging out kills all containers running for this student

## 0.23.0 2019 Oct 31

* change in data model (requires migration):
  courses are attached to groups and no longer users
* users in groups will by default only see the courses
  that are attached to one of their groups; seeing all
  courses remains an option through a bread crumb
* course management page displays all users in all attached
  groups

## 0.22.1 2019 Oct 30

* fine-grained improvements with pull-students, which now performs rather well
* mass-register command can now be used to create groups from the same file format

## 0.22.0 2019 Oct 13

* nbh-manage pull-students now has a logic that allows to merge
  notebooks changed both on the student's side and upstream by teachers
  when a regular git pull does not do the trick, the logic is to
  * do a nbstripout on notebooks changed on both ends
  * create a commit with files changed on both ends
  * merge origin/master on top of that
* jupytext is added in all images
* a notebook present only as a .jupytext/.py file can be opened
  with the same URL as if it were a .ipynb (experimental)

## 0.21.2 2019 Oct 13

* better pull-students; a students that have committed their changes and then merged
  upstream are now considered OK, while former code was just checking hashes were equal
* some work done towards #96, markdown documents can be part of a section in a track
* fixed bug #97, clicking in a section now works as expected
* some progress done towards #77, a group name can be passed along to mass-register,
* and the groups-list management command allows to show groups
* gotten rid of nbgitpuller altogether - #98

## 0.21.1 2019 Sep 30

* bugfix: there was a need to expose the local course's master repo, i.e. the one under
  `courses-git`, so that containers can pull from there

## 0.21.0 2019 Sep 29

* students repos use local mirror as their origin;
  in classroom mode each student has a git repo:
  * prior to this change student repos were cloned from the
    same - external - location as the local course master directory
    in $NBHROOT/courses-git
  * with this change, student repos use the local mirror repo
    in $NBHROOT/courses-git as their 'origin' remote
  this will solve access to private repos (that would otherwise
  require undesirable extra config for each student);
  plus it makes syncing a lot faster of course
* as a side-effect, autopull cycle is reduced to 5 minutes

## 0.20.1 2019 Sep 28

* change in monitor about containers **that** do match our naming policy but that cannot
  be probed in terms of last activity;
  * prior to this change, such containers were left alone; this policy dated back
    to when Jupyter (< 5 IIRC) had no API to probe for running kernels
    and their activity
  * given that Jupyter-5 can be taken for granted, such containers can only be zombies
    that the root context has lost connectivity to; starting with 0.20.1 such containers
    are killed by monitor
* by default monitor now runs every 10'
* bugfix, error 502 was displaying error 404 (because 502.html was missing in the git repo)
* nginx debug no longer turned on by default

## 0.20.0 2019 Sep 25

* new feature to reset one's password

## 0.19.1 2019 Sep 22

* new management command nbh-manage pull-students
* courses-list -l also shows git hash
* core images with a cleaner separation between what is done by root and jovyan;
  allows to resurrect ijavascript kernel
* remove references to nbgitpuller

## 0.18.3 2019 Sep 4

* mass registration with quotes was not removing quotes

## 0.18.2 2019 Sep 3

* bugfix in css selector, that caused safari to not show active track
* mass register input format has support for quoted tokens

## 0.18.1 2019 Aug 26

* nicer error pages, and an attempt to provide more useful feedback
  to users if 502 still triggers

## 0.18.0 2019 Aug 26

* drop support for http #94
* an attempt at addressing #93 - error 502 -
  by increasing some timeouts on the nginx side

## 0.17.6 2019 Aug 26

* bugfix #92

## 0.17.5 2019 Aug 24

* bugfix #91

## 0.17.4 2019 Aug 23

* bugfix #88

## 0.17.3 2019 Aug 23

* bugfix #87

## 0.17.2 2019 Aug 21

* bugfix #86

## 0.17.1 2019 Aug 21

* in classroom mode, could not open notebooks (error 404) for fresh users
* sub-unit notebook border width was causing random rendering

## 0.17.0 2019 Aug 12

* one can write a URL in `/auditor/notebook/course@classic`- or `course@jlab` -
  for direct access to jupyter app
* more consistent UI when switching between tracks or jupyter apps
* as a side effect, we no longer show untracked notebooks
  in track mode, use a jupyter app to manage them
* togglers to go fullscreen can be used independently
  e.g. control-clicking the left one will only hide left panel

## 0.16.7 2019 Aug 2

* bugfix with autopull that couls get stalled

## 0.16.6 2019 Aug 1

* the core images come with more predefined content, namely
  * git user preconfigured, nbgitpuller and jupyterlab-git
  * ipywidgets, and splitcell nbextension
* management commands deal with courses in alphabetical order

## 0.16.5 2019 Aug 1

* courses-list -l
* course-create with no image name uses coursename

## 0.16.4 2019 July 27

* /auditor/courses/?pattern=

## 0.16.3 2019 July 27

* new commands courses-list and course-rename
* deprecate command 'migrate-datamodel'

## 0.16.2 2019 July 11

* checkpoint for upgrading prod box

## 0.16.1 2019 July 1

* new URLs are available to pick between 2 copy policies
  * /notebookLazyCopy (equivalent to legacy ipythonExercice) and
  * /notebookGitRepo (for use in classroom mode, a full git repo gets created)
* monitor to log on stdout for journalctl to pick
* UI: toggle buttons now toggle left and top at the same time
* updated install doc
* some CSS jupyter tweaks are now restricted to not apply in slideshow mode
* light cleanup in nbh sript

## 0.15.2 2019 Jun 16

* fullscreen mode using arrows to hide top and left drawer of auditor notebook view
* heder updated in auditor notebook view when switching notebooks and jupyter modes
* staff usernames (for ignoring stats only) can be entered in the ui
* deprecated nbh course-settings, use the ui

## 0.15.1 2019 Jun 11

* db-backed data model for course details
* form to edit course
* slightly redesigned header

## 0.14.1 2019 Jun 7

* new all-in-one /auditor/notebook view refurbished from scratch
* in particular, this exposes nbgitpuller (required on the image though)
* /auditor/course and /auditor/jupyterdir both go down the sewer

## 0.14.0 2019 Jun 3

* refactored build of core images, remove the need for duplication of gory details
* no longer needs to downgrade tornado, await works just fine
* standard image now include our custom nbgitpuller

## 0.13.1 2019 May 3

* toplevel url in <https://nbhosting.inria.fr/> works now
* new all-in-one command nbh-manage create-course
* nicer staff courses page

## 0.13.0 2019 Apr 20

* IMPORTANT fix about the way to configure docker-ce; change in 0.12.1 was incomplete,
  so docker would not be configured to use disk space under NBHROOT
* location of the database has changed as well, now searched under NBHROOT too
* globally more robust in terms of parametrization of NBHROOT,
  as our dev box now actually uses an alternate location
  so as to ease up pivoting when swapping dev and prod

## 0.12.2 2019 Apr 18

* fix regression introduced when dealing with filenames with spaces;
  was resulting in duplicated .ipynb extensions all over the place
* more consistent color scheme for the UI
  blue is for track-based; green for file-based; red for managements and orange for stats
* untracked notebooks show up correctly
  both jupyter classic and lab are available
* fixed stats for courses that use non-edx name scheme for user hashes

## 0.12.1 2019 Apr 11

* migration to docker-ce instead of formerly docker-1.13; see fedora/migrate-to-docker-ce.md
* updated install_requires
* bugfix: notebooks with space in their name were problematic
* classroom mode: show notebooks present in the student's workdir but not in track
* classroom mode: the jupyterdir feature allows to browse workdir in raw jupyter mode
* better copyToClipboard for sharing static snapshot

## 0.11.1 2019 Mar 18

* in auditor mode, iframe gains focus at once, no longer need to click
* all config tweaks like static mappings or dockerfile
  can appear in $NBHROOT/local (preferred) or in course's `nbhosting` subdir
* new `destroy my container` feature in staff course view
* which by the way is reorganized a little
* rough mass registration script available; passwords get sent by email
* new command `build-core-images` allows to produce 2 docker images that are nbhosting-ready:
  * `nbhosting/minimal-notebook`
  * and `nbhosting/scipy-notebook`
* more commands like e.g. `course-build-image` and `monitor` are now written in python rather than bash; shell command `nbh` is still available, but some commands must be triggered through `nbh-manage` that is a copy of toplevel `manage.py`; probably a little awkward but that's the current status; hence `nbh-monitor` has gone as a command, still relevant as a service though
* source code has a new layout, less awkward to run in devel mode

## 0.10.1 2019 Mar 12

* refactored a new source code layout, resulting in much cleaner imports,
  and the ability to invoke django-defined management commands from `/usr/bin/nbh-manage`

## Jan 2018

We've admittedly been rather sloppy wrt versioning here. The thing is the code
gets deployed on both `nbhosting.inria.fr` and its sistership
`nbhosting-dev.inria.fr` directly from the public repo on github.

## 0.1.0 - 2017 Apr 27

* first versioned release
