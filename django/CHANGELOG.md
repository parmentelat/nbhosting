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
  can appear in `/nbhosting/local` (preferred) or in course `nbhosting` subdir
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
