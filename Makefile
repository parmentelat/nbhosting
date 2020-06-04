pypi:
	$(MAKE) -C django pypi

####################
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -ai $(RSYNC_COND_DRY_RUN)
# the list of files either in the index, or modified
NEWS 			= $(shell (git diff --name-only; git diff --name-only --cached) | sort -u)
GIT-FILES		= $(shell git ls-files)

DEVBOX = root@nbhosting-dev.inria.fr
PRODBOX = root@nbhosting.inria.fr
TESTBOX = root@stupeflip.pl.sophia.inria.fr

### push just the files that have changed
syncdev:
	+$(RSYNC) --relative $(NEWS) $(DEVBOX):nbhosting/
syncprod:
	+$(RSYNC) --relative $(NEWS) $(PRODBOX):nbhosting/
synctest:
	+$(RSYNC) --relative $(NEWS) $(TESTBOX):git/nbhosting/


# using git ls-files -m is nice, but sometimes it's too picky
syncdev+:
	+$(RSYNC) --relative $(GIT-FILES) $(DEVBOX):nbhosting/
syncprod+:
	+$(RSYNC) --relative $(GIT-FILES) $(PRODBOX):nbhosting/
synctest+:
	+$(RSYNC) --relative $(GIT-FILES) $(TESTBOX):git/nbhosting/
