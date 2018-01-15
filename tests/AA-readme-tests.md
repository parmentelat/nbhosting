# Setup

* one test server (typically nbhosting-dev.inria.fr)
  * no special requirement more than being installed and ready

* one test box (typically darktek.pl.sophia.inria.fr)
  * requires selenium - `pip install selenium`
  * requires nepi-ng - `pip install asyncssh asynciojobs apssh`

# Preparation

Optional but helpful

    root@thermals ~ # nbh list-tests

and

    root@thermals ~ # nbh clear-tests



# Typical use

### fire from a linux box

I have used the root account on `darktek.pl.sophia.inria.fr`:

```
root@darktek ~ #
cd git/nbhosting/
git pull
cd tests
```

### record disk usage beforehand
```
root@thermals ~/nbhosting/tests (master *$=) # df -hT /nbhosting/
Filesystem     Type   Size  Used Avail Use% Mounted on
/dev/sda3      btrfs  1.1T   28G  1.1T   3% /nbhosting
```

see also

```
nbh status-btrfs
```

### clean artifacts from previous runs

on your mac

    ~/git/nbhosting/tests (devel $=) $ rm -rf artefacts-darktek

on the linux worker

    root@darktek ~/git/nbhosting/tests (devel=) # rm -rf artefacts    


### check it out

dry run first to check your sitesettings

    ./nbhtests -n


### my first 100-students batch - one notebook per student

    root@darktek ~/git/nbhosting/tests # ./nbhtests -m -u 1-100


Because we have set `-m`, then **only one** notebook is rando**m**ly picked for each student (among the complete set found in that course); one can add `-i 0-11` if the notebooks are to be selected in a specific, narrower range.

### several notebooks per student

```
root@darktek ~/git/nbhosting/tests # ./nbhtests -i 1-3 -u 1-100
```

Using an index range like this **without `-m`** will run these 3 notebooks for each of the 100 students.

### unattended mode

    nohup ./nbhtests -m -u 1-100 -p 10 >& TESTS.log & exit

### use another course

By default we use `~/git/flotpython3` as the root of the course tree; it is used in particular to make up the notebook names, so this needs to be in sync with what the test server sees. **NOTE** that in particular it should use the **same course name** as on the server.

Use this to use another course tree.

    -c ~/git/flotpython3

### use another server

Default for the test server is `https://nbhosting-dev.inria.fr/`, can be changed like this:

    -U https://nbhosting-dev.inria.fr/

### speed it up

    The default period is like 20s, to go twice as fast just add

        -p 10

# Dealing with results

### get them back

from my local (macbook pro) laptop, I can gather the results back from darktek by doing

```
parmentelat ~/git/nbhosting/tests $ ./darktek.fetch
```

Which retrieves the relevant files from darktek in `./artefacts-darktek`.
**Beware** however that this is cumulative.

### what to expect

* The `.txt` files should exist for all students; they should show something like

```
parmentelat ~/git/nbhosting/tests $ cat artefacts-darktek/student-0001-flotpython-8-contents-4contents.txt
kernel area:[]
number of cells: 18
```
