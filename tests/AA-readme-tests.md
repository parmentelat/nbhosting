# Important note

as of 2019 nov 15, darktek is being decommissioned and goes into the r2lab room; 
our new test box will thus be **`stupeflip`** (Command-2); 
here's a summary of the steps I have taken to set it up,
starting from a rther mundame fedora-29,
in a hope to better understand that fonts thing

```
cd
mkdir git
cd git
# populate with nbhosting + 5 courses
git clone https://github.com/parmentelat/flotbioinfo.git bioinfo
git clone https://github.com/flotpython/gittutorial.git mines-git-tuto
git clone https://github.com/flotpython/primer mines-python-primer
git clone https://github.com/parmentelat/nbhosting.git nbhosting
git clone https://github.com/flotpython/slides.git python-slides
git clone https://github.com/parmentelat/flotpython.git python3-s2

pip3 install selenium
dnf install -y chromedriver
dnf install -y chromium
```

and at that point everything was working fine.. For good measure I added also

```
dnf install mathjax
```


# Setup

* one test server (typically nbhosting-dev.inria.fr)
  * no special requirement more than being installed and ready

* one test box (typically darktek.pl.sophia.inria.fr)
  * requires selenium - `pip3 install selenium`
  * requires nepi-ng - `pip3 install asyncssh asynciojobs apssh`
  * requires requests - `pip3 install requests`

* courses
  * check that course `python3-s2` is defined in the nbhosting server, and that
    on the test box there is a git repo by that name 


**UPDATE 2019 Nov**

* phantomJS has been deprecated under selenium
* so I had to do  
  `dnf install chromium chromedriver chromium-libs-media`
  `dnf install xorg-x11-fonts-misc xorg-x11-font-utils`
* NOTE: I had to struggle quite some time for getting the fonts to work; I even went to
  upgrading to fedora-30 in the mix, but not sure what actually fixed that issue; best
  guess is that is was a matter of installing the x11 fonts and rebooting, but that would
  need confirmation

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

By default we use `~/git/python3-s2` as the root of the course tree; it is used in particular to make up the notebook names, so this needs to be in sync with what the test server sees. **NOTE** that in particular it should use the **same course name** as on the server.

Use this to use another course tree.

    -c ~/git/python3-s2

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
parmentelat ~/git/nbhosting/tests $ cat artefacts-darktek/student-0001-python3-s2-8-contents-4contents.txt
kernel area:[]
number of cells: 18
```
