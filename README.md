# notebook hosting architecture

This git repo contains a collection of utilities, that together make up the architecture behind `nbhosting.inria.fr` that is designed as a notebook-serving infrastructure.

First use case is for hosting notebooks in the context of MOOCs. See e.g.

* [Python : des fondamentaux à l'utilisation du langage on fun-mooc.fr](https://www.fun-mooc.fr/courses/inria/41001S03/session03/about)
* [Bioinformatique : algorithmes et génomes on fun-mooc.fr](https://www.fun-mooc.fr/courses/inria/41003S02/session02/about)

******

# *Open-edX* teacher side

On the edx side, teacher would create a bloc typed as *ipython notebook* - note that the present repo does not address the code for the edx extension that supports this type of blocs (ref?); it is readily available at this point (jan. 2017) at `fun-mooc.fr`; see below for enabling it on a new course.

![](docs/edx-bloc.png)

![](docs/edx-notebook.png)

![](docs/edx-details.png)

******

# *Open-edX* student side

Here's what a student would see;

![](docs/edx-student.png)

******

# Miscellaneous

## Enabling `New ipython notebook`

Before you can, as a teacher, add your first notebook-backed content in your edx
course, you need to enable that extension; in order to do that, go to Studio,
and then in your course's *Settings* → *Avanced*, and add `ipython` the *Avanced
Module List* setting, as illustrated below:

![](docs/edx-enable-ipython.png)

## Workflow / how to publish

Workflow is entirely based on git : a course is defined from a git repo, typically remote and public. In order to publish a new version of your notebook, you need to push them to that reference repo, and then instruct nbhosting to pull the new stuff:

![](docs/nbhosting-git-pull.png)

## Docker image

Each course is deployed based on a specific docker image; for customization,
create a file named `docker-image/nbhosting.Dockerfile` in your course repo.
Note that some magic recipes need to be applied in your image for proper
deployment, you should copy the beginning of [the code for our Python
course](https://github.com/parmentelat/flotpython/blob/master/docker-image/nbhosting.Dockerfile),
although it is often desirable to select a fixed version for the bottom image.

That image can then be rebuilt from the website. New image will be deployed
incrementally, essentially as running containers get phased out when detected as
inactive; this means it can take a day or two before all the students can see
the upgrade.

![](docs/nbhosting-rebuild-image.png)


## Statistics

Statistics are available, for visually inspecting data like:
* how many different students have showed up and when,
* which notebooks were opened and when,
* computing resources like created/active containers, disk space, CPU load...

![](docs/nbhosting-stats.png)


******

# Dataflow - `nbhosting` side

Here's the general principle of how of works

* Open-edX forges a URL, like the one shown above, with `student` replaced with the hash of some student id
* This is caught by nginx, that runs forefront; the `ipythonExercice/` prefix is routed to a django application, that primarily does this
  * create a linux user if needed
  * create a copy of that notebook for the student if needed
  * spawns a (docker) jupyter instance for the couple (course, student)
  * redirects to a (plain https, on port 443) URL that contains the (http/localhost) port number that the docker instance can be reached at

As a summary:

![](docs/architecture.png)



# TODO

See [Issues on github](https://github.com/parmentelat/nbhosting/issues) for an up-to-date status.
