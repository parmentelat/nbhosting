# container images

This document describes how to manage the image built for each course.

# the `docker-stacks` images

So far we have been using images based on one of the `docker-stacks` images - see https://github.com/jupyter/docker-stacks  - and mostly on `scipy-notebook`

To select an image, see https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html, and remember these relationships

![](inherit-diagram.png)


This being said, as of March 2019, the scipy-notebook image is lingering behind with still Python-3.6 which is a nuisance.

See also [`docker-stacks.md`](docker-stacks.md) in the current directory for additional notes on the various images.

# nbhosting, images, and uids

In order to get each user-created notebook properly stored in the host, i.e. with the right uid, there currently (dec. 2017) is a need to tweak the images as provided by docker-stacks.

In particular, instead of starting the container through `start.sh` as provided by docker-stacks, we use our own starter script named `start-in-dir-as-uid.sh` (source code in the current directory as well).


### nbhosting-derived images

For convenience we provide 2 base images

| nbhosting name | based on |
|----------------|----------|
| nbhosting/scipy-notebook | jupyter/scipy-notebook |
| nbhosting/minimal-notebook | jupyter/minimal-notebook |

These images have the docker-stacks images prepared for nbhosting.
Using them is not mandatory, but again having `start-in-dir-as-uid.sh` installed in `/usr/local/bin` is a **strong requirement**, if only for performance reasons.

These nbhosting images are **not** published on dockerhub, instead they are meant to be redone locally before rebuilding course images; to this end, do

```bash
nbh-manage build-images
```


# course settings

In `nbhosting`, each course uses a specific image; all students in the same course have a container based on the same image.

So each course has an `image` name  associated to it; by default the image name is the same as the course name, but this can be altered in the web UI.

A course has several options:

* either is uses some other image (that is to say, its imagename **does not
 match** the course name); trying to rebuild the image for a course that falls
 into this first category will result in an error.

* or it wants to describe its own image (when its imagename **does match** its own name); in that case, a `Dockerfile` is searched in 2 locations:
  * first in
   `$NBHROOT/local/<coursename>/Dockerfile`
  * then in the course repo itself, that is in
  `$NBHROOT/courses-git/<coursename>/nbhosting/Dockerfile`

In that second case, rebuilding a course's image is thus generally done either

* through the web UI: update from git, then rebuild image
* from the shell, through the following steps:

```bash
nbh course-pull mycourse
nbh-manage course-build-image mycourse
```

Whatever the option among the 2 discussed above, the important thing is for a course to pick a name that is
* **a valid container image name**
* that is built **on top** of one of the **core nbhosting images**, as these contain crucial utilities.


# deployment logic

The logic implemented for rolling out images has 2 aspects, whether it is at runtime, or at image-building time.

### runtime


* when a student shows up, if its container already exists (running or not), it is used as-is; otherwise it is created from the course image.

* for rolling out image updates: some important thing happens also when a student is considered idle by the monitor (after some inactivity). At that point, the hash of the running (and about to be stopped) container is compared with the one that the student container **should be based on** (i.e. if we created it at that time). If they don't match the student container gets **removed** altogether instead of just being killed. This way next time the student show up her container will be created based on the 'right' image.

### image-building time

* note that there may be a need to explicitly call `podman pull` beforehand, if an upgrade of the base images is desired.

* assuming the course's imagename matches its name (otherwise, course-build-image will cowardly refuse to do anything), a Dockerfile is searched as described above.

In any case, the image-building command is run in a directory that contains:

* the dockerfile as located above,
* and in any case the `start-in-dir-as-uid.sh` script, in the current `images/` subdir of `nbhosting`, as this is a key part of the whole business.

Your dockerfile **MUST** copy `start-in-dir-as-uid.sh` in the images's `/usr/local/bin`; it **must** also run as root; `because start-in-dir-as-uid.sh` needs this privilege in order to setuid as the actual student uid; see as an example [the dockerfile for the python MOOC](https://github.com/parmentelat/flotpython/blob/master/nbhosting/Dockerfile).

**Final note** in the `Dockerfile` for `python-mooc` we have chosen to use the ***latest*** version of `scipy-notebook` image. This is on purpose, but not necessarily the best practice if you want to be on the safe side, and be resilient to hasty upgrades on dockerhub; so you may what to use a specific image hash instead.

# conclusion

The objectives that we had here, and that are fulfilled with this implementation, are that:

* each course can provide its own image specification,
* the administrator can also override this with a home-cooked container image specification - this is for example for running course based on material that was not written for nbhosting, like e.g. DataScienceHandbook (it's true that a git fork could work around that issue, but well)
* we can leverage dockerhub images and standard building tools
* and easily roll out upgraded course images with minimal impact for students.
