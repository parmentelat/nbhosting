# Preparation

Optional but helpful

```
root@thermals ~ # nbh clear
clearing log file /var/log/nginx/*.log
```

# Typical use

## fire from a linux box

I have used the root account on `darktek.pl.sophia.inria.fr`:

```
root@darktek ~ # 
cd git/nbhosting/
git pull
cd tests
```

## record disk usage beforehand
```
root@thermals ~/nbhosting/flavours-docker # df -h /homefs/btrfs
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda7       359G  8.7G  349G   3% /homefs/btrfs
```

and/or

```
nbh status-btrfs
========== btrfs filesystem df -h /homefs/btrfs/machines
Data, single: total=22.00GiB, used=20.04GiB
System, DUP: total=8.00MiB, used=16.00KiB
Metadata, DUP: total=4.50GiB, used=4.02GiB
GlobalReserve, single: total=272.28MiB, used=0.00B
========== btrfs filesystem df -h /homefs/btrfs/btrfs
Data, single: total=22.00GiB, used=20.04GiB
System, DUP: total=8.00MiB, used=16.00KiB
Metadata, DUP: total=4.50GiB, used=4.02GiB
GlobalReserve, single: total=272.28MiB, used=0.00B
```

## a 100 students batch

### typical: one notebook per student

```
root@darktek ~/git/nbhosting/tests # ./nbhtests -m -u 1-100 
```

Because we have set `-m`, then only one notebook is picked for each student (among the complete set found in that course); one can add `-i 0-11` (week 1 in this case) if the notebooks are to be selected in a narrower range.

### several notebooks per student

```
root@darktek ~/git/nbhosting/tests # ./nbhtests -i 1-3 -u 1-100 
```

Using an index range like this **without `-m`** will run these 3 notebooks for each of the 100 students.

## speed it up

The default period is like 20s, to go twice as fast just add

    -p 10

## use another course

The `-c` option expects the root of a course tree, like e.g.

    -c ~/git/flotbioinfo

## get results back

from my local (macbook pro) laptop, I can gather the results back from darktek by doing

```
parmentelat ~/git/nbhosting/tests $ ./darktek.fetch
```

Which retrieves the relevant files from darktek in `./artefacts-darktek`. 
**Beware** however that this is cumulative.

## results

* The `.txt` files should exist for all students; they should show something like

```
parmentelat ~/git/nbhosting/tests $ cat artefacts-darktek/student-0001-flotpython-8-contents-4contents.txt
kernel area:[]
number of cells: 18
```
