# docker images

Here is how to deal with docker images for the various courses hosted in a `nbhosting` instance.

# the `docker-stacks` images

So far we have been using only images based on one of the `docker-stacks` images - see https://github.com/jupyter/docker-stacks - and mostly on `scipy-notebook`

See also [`dockers-stacks.md`](docker-stacks.md) in the current directory for additional notes on the various images.

# nbhosting, docker, et uids

In order to get each user-created notebook properly stored in the host, i.e. with the right uid, there currently (dec. 2017) is a need to patch the images as provided by docker-stacks.

In particular, instead of starting the container through `start.sh` as provided by docker-stacks, we use our own starter script named `start-in-dir-as-uid.sh` (source code in the current directory as well).


# how should each course describe its notebook environment

The paradigm used in `nbhosting` is simply that each course uses a specific image; this way all students have a container based on the same image.

The logic implemented at this point has 2 aspects, whether it is at runtime, or at image-building time.

### runtime

* each course has an 'image' name associated to it; by default the image name is the same as the course name, but this can be altered with `nbh course-settings -i imagename coursename`.

* when a student shows up, if its container already exists (running or not), it is used as-is; otherwise it is created from the course image.

* for rolling out image updates: some important thing happens also when a student is considered idle by the monitor (after some inactivity). At that point, the hash of the running (and about to be stopped) container is compared with the one that the student container **should be based on** (i.e. if we created it at that time). If they don't match the student container gets **removed** altogether instead of just being killed. This way next time the student show up her container will be created based on the 'right' image.

### image-building time

* the command `nbh update-image imagename` allows an administrator to do or redo the image of that name.

* for that purpose, a dockerfile is needed (here we assume the course and image names match):

  * first we search for a directory named `docker-image` in the course contents. If found, it should contain a file named `nbhosting.Dockerfile`.

  * otherwise we search inside `nbhosting/images` for a file named `imagename`.dockerfile

In any case, the docker-building command is run in a directory that contains:

* the dockerfile as located above,
* all the contents of `course/docker-image` if that's where the dockerfile was found,
* and in any case the `start-in-dir-as-uid.sh` script, in the current `images/` subdir of `nbhosting`, as this is a key part of the whole business.

Your docker file **MUST** copy `start-in-dir-as-uid.sh` in the images's `/usr/local/bin`; it **must** also run as root; `because start-in-dir-as-uid.sh` needs this privilege in order to setuid as the actual student uid; see as an example [the dockerfile for the python MOOC](https://github.com/parmentelat/flotpython/blob/master/docker-image/nbhosting.Dockerfile).

**Final note** in the `dockerfile` for `flotpython` we have chosen to use the latest `scipy-notebook` image. This is on purpose, but not necessarily the best practice if you want to be on the safe side, and be resilient to hasty upgrades on dockerhub; so you may what to use a specific image hash instead.

# conclusion

The objectives that we had here, and that are fulfilled with this implementation, are that:

* each course can provide its own docker-image specification,
* the administrator can also a docker image specification - this is for example for running course based on material that was not written for nbhosting, like e.g. DataScienceHandbook (it's true that a git fork could work around that issue, but well)
* we can still leverage docker's image building tools
* and easily roll out upgraded course images with minimal impact for students.
