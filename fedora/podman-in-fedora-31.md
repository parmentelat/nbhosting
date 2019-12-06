# upgrading to fedora-31

The unexpected bad news is that `docker-ce` won't work as-is on fedora-31; apparently
docker does not yet support cgroups-v2, which fedora-31 enables by default. So long story
short there is no easy way to install that stuff on fedora-31.

The unexpected good news is that `podman` is available on fedora-31 right out of the
vanilla repo; it does support cgroup-v2, and has a compatible CLI interface; 
so add to that the fact that our fedora-29 deployment is exhibiting really weird 
and odd behaviour, replacing docker with podman is definitely worth a try.

# notes


* docker not available
  * stopped and uninstalled `docker-ce` 
  * could have (but delayed) disabled the `docker-ce` repos in `/etc/yum.repos.d`
  * instead installed `podman`, `podman-docker`

* storage layout
  * created /nbhosting/containers
  * edited /etc/containers/storage.conf  
    `graphroot = "/var/lib/containers/storage"`

* the `btrfs` driver note on failed attempt
  * since we used to run on btrfs, and that the underlying partition under `/nbhosting` 
    is a btrfs partition, at some point I figured I'd give a try with the 'btrfs' driver
  * first off, it's a pain because essentially I had to clean up `/nbhosting/containers` completely
  * second, it turned out podman essentially refused to work altogether; 
    I could not even run `podman ps` nor `podman pull` with this setup, so I rolled back to
    using `driver = "overlay"`, which is the default (and corresponds to docker's `overlay2` thing)

* rebuilt images
  * `nbh-manage build-core-images`
  * `nbh-manage course-build-image --all`
  * one image (data-science-handbook I believe) could not build when updating conda; 
    there was a question asked and it seemed like the answer was not taken into account 
    and the image building process looked like it was hanging - to be double-checked

    **LESSON LEARNED** run conda installation / update scripts with `-y`

# todo

## detach mode

* I am observing a very odd behaviour; when trying to spawn a container from a 
  distant web browser, django issues a call to nbh to kick off the podman container
* when invoked through that route, the `podman run` process hangs and never returns - even
  though it has the `--detach` option all right
* in addition at that point, that hanging process seems to prevent anything else from
  accessing the podman API, so e.g. a simple `podman ps` would hang as well

* the same `podman run` command, when copied and pasted into a terminal, seems to behave
  as expected : it prints out a container hash, and returns
* running the complete `nbh` command (example below) from a terminal, also works
  fine, i.e. does not block

```
student=student-0002
nbh -d /nbhosting/current -x docker-view-student-course-notebook $student python3-s2 w1/w1-s1-av.ipynb python3-s2 https://github.com/flotpython/course.git
```

```
port=41317
student=student-0003
ls /nbhosting/dev/students/$student/python3-s2
ss -l -t -n | grep $port

podman run --name python3-s2-x-$student -p $port:8888 --user root --rm --detach --env NBAUTOEVAL_LOG=/home/jovyan/work/.nbautoeval -v /nbhosting/dev/students/$student/python3-s2:/home/jovyan/work -v /nbhosting/dev/jupyter/python3-s2/jupyter_notebook_config.py:/home/jovyan/.jupyter/jupyter_notebook_config.py:ro -v /nbhosting/dev/jupyter/python3-s2:/home/jovyan/.jupyter/custom:ro -v /nbhosting/dev/modules/python3-s2:/home/jovyan/modules:ro -v /nbhosting/dev/static/python3-s2:/home/jovyan/static:ro -v /nbhosting/dev/courses-git/python3-s2:/nbhosting/dev/courses-git/python3-s2:ro -e PYTHONPATH=/home/jovyan/modules python3-s2 start-in-dir-as-uid.sh /home/jovyan 100321 jupyter notebook --ip=0.0.0.0 --no-browser --NotebookApp.notebook_dir=/home/jovyan/work --NotebookApp.token=python3-s2-x-$student --NotebookApp.base_url=/$port/ --log-level=DEBUG
```  

# monitor

* the monitor no longer works, it needs to be tweaked
* about that, I am starting to suspect that, on our production platform, most of the
  undesired behaviour might be related to monitor; I'm thinking that it could be somehow
  interfering if it uses the access to the docker daemon too much; it could be worth
  investigating, for example by turning off the monitor temporarily.
