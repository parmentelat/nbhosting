TESTBOX=root@nbhosting.pl.sophia.inria.fr

SYNC_PATHS = frontend manage.py nbhosting scripts

sync:
	rsync -av $(SYNC_PATHS) $(TESTBOX):nbhosting-sync

