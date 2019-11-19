LIBRARY = nbhosting

VERSION = $(shell python3 django/setup.py --version)
VERSIONTAG = $(LIBRARY)-$(VERSION)
GIT-TAG-ALREADY-SET = $(shell git tag | grep '^$(VERSIONTAG)$$')
# to check for uncommitted changes
GIT-CHANGES = $(shell echo $$(git diff HEAD | wc -l))

# we don't push to pypi, just set a release tag
release:
	@if [ $(GIT-CHANGES) != 0 ]; then echo "You have uncommitted changes - cannot publish"; false; fi
	@if [ -n "$(GIT-TAG-ALREADY-SET)" ] ; then echo "tag $(VERSIONTAG) already set"; false; fi
	@if ! grep -q ' $(VERSION)' django/CHANGELOG.md ; then echo no mention of $(VERSION) in CHANGELOG.md; false; fi
	@echo "You are about to release $(VERSION) - OK (Ctrl-c if not) ? " ; read _
	git tag $(VERSIONTAG)
	#./setup.py sdist upload -r pypi

version:
	@echo $(VERSION)

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
