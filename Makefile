TESTBOX=root@nbhosting.pl.sophia.inria.fr

SYNC_PATHS = edxfront manage.py nbhosting scripts

sync:
	rsync -av $(SYNC_PATHS) $(TESTBOX):nbhosting-sync
	rsync -av nginx/nbhosting.conf $(TESTBOX):/etc/nginx/conf.d/
	ssh $(TESTBOX) systemctl restart nginx
	rsync -av uwsgi/nbhosting.ini $(TESTBOX):/etc/uwsgi.d/
	rsync -av uwsgi/nbhosting.service $(TESTBOX):/etc/systemd/system/
	ssh $(TESTBOX) systemctl restart nbhosting

