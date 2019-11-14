# 0.24.4 2019 Nov 14

* fix the jupyter classic/lab buttons

# 0.24.3 2019 Nov 14

* increase timeout when spawning containers from 12 to 20s

# 0.24.2 2019 Nov 13

* 0.24 is good to go 
* minor tweak to smooth migration: stopped containers, sequels of a pre-0.23 deployment,
  are killed before returning an error
* tests are operational again, running on a headless chromium

# 0.24.1 2019 Nov 8

* simplified container creation code now that containers are 
  deemed oneshot, and destroyed after their idle time
* removed --unused option in monitor which is now meaningless

# 0.24.0 2019 Nov 7

* major rework of the overall routing scheme
* no longer relies on cookies to route properly !
* which in turn makes multi-course sessions a lot more reliable
* see issue #102 and commit 8faa38 

# 0.23.2 2019 Nov 4

* cosmetic tweaks in the staff course view 
  when showing members of the groups attached to a course

# 0.23.1 2019 Nov 4

* close #100: logging out kills all containers running for this student

# 0.23.0 2019 Oct 31

* change in data model (requires migration):
  courses are attached to groups and no longer users
* users in groups will by default only see the courses
  that are attached to one of their groups; seeing all
  courses remains an option through a bread crumb
* course management page displays all users in all attached
  groups

# 0.22.1 2019 Oct 30

* fine-grained improvements with pull-students, which now performs rather well
* mass-register command can now be used to create groups from the same file format

# 0.22.0 2019 Oct 13

* nbh-manage pull-students now has a logic that allows to merge 
  notebooks changed both on the student's side and upstream by teachers
  when a regular git pull does not do the trick, the logic is to
  * do a nbstripout on notebooks changed on both ends
  * create a commit with files changed on both ends
  * merge origin/master on top of that
* jupytext is added in all images
* a notebook present only as a .jupytext/.py file can be opened
  with the same URL as if it were a .ipynb (experimental)


# 0.21.2 2019 Oct 13

* better pull-students; a students that have committed their changes and then merged 
  upstream are now considered OK, while former code was just checking hashes were equal
* some work done towards #96, markdown documents can be part of a section in a track
* fixed bug #97, clicking in a section now works as expected
* some progress done towards #77, a group name can be passed along to mass-register,
* and the groups-list management command allows to show groups
* gotten rid of nbgitpuller altogether - #98


# 0.21.1 2019 Sep 30

* bugfix: there was a need to expose the local course's master repo, i.e. the one under
  `courses-git`, so that containers can pull from there

# 0.21.0 2019 Sep 29

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

# 0.20.1 2019 Sep 28

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

# 0.20.0 2019 Sep 25

* new feature to reset one's password

# 0.19.1 2019 Sep 22

* new management command nbh-manage pull-students 
* courses-list -l also shows git hash
* core images with a cleaner separation between what is done by root and jovyan;
  allows to resurrect ijavascript kernel
* remove references to nbgitpuller

# 0.18.3 2019 Sep 4

* mass registration with quotes was not removing quotes

# 0.18.2 2019 Sep 3

* bugfix in css selector, that caused safari to not show active track
* mass register input format has support for quoted tokens

# 0.18.1 2019 Aug 26

* nicer error pages, and an attempt to provide more useful feedback
  to users if 502 still triggers

# 0.18.0 2019 Aug 26

* drop support for http #94
* an attempt at addressing #93 - error 502 - 
  by increasing some timeouts on the nginx side

# 0.17.6 2019 Aug 26

* bugfix #92

# 0.17.5 2019 Aug 24

* bugfix #91

# 0.17.4 2019 Aug 23

* bugfix #88

# 0.17.3 2019 Aug 23

* bugfix #87

# 0.17.2 2019 Aug 21

* bugfix #86

# 0.17.1 2019 Aug 21

* in classroom mode, could not open notebooks (error 404) for fresh users
* sub-unit notebook border width was causing random rendering

# 0.17.0 2019 Aug 12

* one can write a URL in `/auditor/notebook/course@classic` 
  - or `course@jlab` - for direct access to jupyter app
* more consistent UI when switching between tracks or jupyter apps
* as a side effect, we no longer show untracked notebooks 
  in track mode, use a jupyter app to manage them
* togglers to go fullscreen can be used independently
  e.g. control-clicking the left one will only hide left panel


# 0.16.7 2019 Aug 2

* bugfix with autopull that couls get stalled

# 0.16.6 2019 Aug 1

* the core images come with more predefined content, namely
  * git user preconfigured, nbgitpuller and jupyterlab-git
  * ipywidgets, and splitcell nbextension
* management commands deal with courses in alphabetical order

# 0.16.5 2019 Aug 1

* courses-list -l
* course-create with no image name uses coursename 

# 0.16.4 2019 July 27

* /auditor/courses/?pattern=

# 0.16.3 2019 July 27

* new commands courses-list and course-rename
* deprecate command 'migrate-datamodel'

# 0.16.2 2019 July 11

* checkpoint for upgrading prod box

# 0.16.1 2019 July 1

* new URLs are available to pick between 2 copy policies
  * /notebookLazyCopy (equivalent to legacy ipythonExercice) and
  * /notebookGitRepo (for use in classroom mode, a full git repo gets created)
* monitor to log on stdout for journalctl to pick
* UI: toggle buttons now toggle left and top at the same time
* updated install doc
* some CSS jupyter tweaks are now restricted to not apply in slideshow mode
* * light cleanup in nbh sript

# 0.15.2 2019 Jun 16

* fullscreen mode using arrows to hide top and left drawer of auditor notebook view
* heder updated in auditor notebook view when switching notebooks and jupyter modes
* staff usernames (for ignoring stats only) can be entered in the ui
* deprecated nbh course-settings, use the ui

# 0.15.1 2019 Jun 11

* db-backed data model for course details
* form to edit course
* slightly redesigned header

# 0.14.1 2019 Jun 7

* new all-in-one /auditor/notebook view refurbished from scratch
* in particular, this exposes nbgitpuller (required on the image though)
* /auditor/course and /auditor/jupyterdir both go down the sewer

# 0.14.0 2019 Jun 3

* refactored build of core images, remove the need for duplication of gory details
* no longer needs to downgrade tornado, await works just fine
* standard image now include our custom nbgitpuller

# 0.13.1 2019 May 3

* toplevel url in https://nbhosting.inria.fr/ works now
* new all-in-one command nbh-manage create-course
* nicer staff courses page

# 0.13.0 2019 Apr 20

* IMPORTANT fix about the way to configure docker-ce; change in 0.12.1 was incomplete, 
  so docker would not be configured to use disk space under NBHROOT
* location of the database has changed as well, now searched under NBHROOT too
* globally more robust in terms of parametrization of NBHROOT, 
  as our dev box now actually uses an alternate location 
  so as to ease up pivoting when swapping dev and prod

# 0.12.2 2019 Apr 18

* fix regression introduced when dealing with filenames with spaces; 
  was resulting in duplicated .ipynb extensions all over the place
* more consistent color scheme for the UI
  blue is for track-based; green for file-based; red for managements and orange for stats
* untracked notebooks show up correctly
  both jupyter classic and lab are available
* fixed stats for courses that use non-edx name scheme for user hashes

# 0.12.1 2019 Apr 11

* migration to docker-ce instead of formerly docker-1.13; see fedora/migrate-to-docker-ce.md
* updated install_requires
* bugfix: notebooks with space in their name were problematic
* classroom mode: show notebooks present in the student's workdir but not in track
* classroom mode: the jupyterdir feature allows to browse workdir in raw jupyter mode
* better copyToClipboard for sharing static snapshot

# 0.11.1 2019 Mar 18

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

# 0.10.1 2019 Mar 12

* refactored a new source code layout, resulting in much cleaner imports,
  and the ability to invoke django-defined management commands from `/usr/bin/nbh-manage`

# Jan 2018

We've admittedly been rather sloppy wrt versioning here. The thing is the code
gets deployed on both `nbhosting.inria.fr` and its sistership
`nbhosting-dev.inria.fr` directly from the public repo on github.

# 0.1.0 - 2017 Apr 27

* first versioned release
