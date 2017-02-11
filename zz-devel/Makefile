# what we used at the beginning for pushing code onto nbhosting
# probably not quite right any longer...

all:
	@echo WARNING - this Makefile probably no longer right

TESTBOX=root@nbhosting.inria.fr

sync:
	@echo 'cd /tmp/nbhosting-sync/django/; export PATH=/tmp/nbhosting-sync/scripts/:$$PATH; export PYTHONPATH=/tmp/nbhosting-sync/django'
	@echo 'systemctl stop nginx; systemctl stop nbh-uwsgi; manage.py runserver thermals:80'
	(cd ..;	rsync -rltpv --relative $$(git ls-files) $(TESTBOX):/tmp/nbhosting-sync/)



