# what we used at the beginning for pushing code onto nbhosting
# probably not quite right any longer...

all:
	@echo WARNING - this Makefile probably no longer right

TESTBOX=root@nbhosting.inria.fr

sync:
	rsync -rltpv --relative $$(git ls-files) $(TESTBOX):/tmp/nbhosting-sync/



