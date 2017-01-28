TESTBOX=root@nbhosting.pl.sophia.inria.fr

SYNC_PATHS = edxfront manage.py nbhosting scripts ports images


sync:
	rsync -rltpv $(SYNC_PATHS) $(TESTBOX):nbhosting-sync
	ssh $(TESTBOX) rsync -av nbhosting-sync/scripts/nbh-\* /usr/bin
	rsync -rltpv nginx/nbhosting.conf.http-only $(TESTBOX):/etc/nginx/conf.d/nbhosting.conf
	ssh $(TESTBOX) systemctl restart nginx
	rsync -rltpv uwsgi/nbhosting.ini $(TESTBOX):/etc/uwsgi.d/
	rsync -rltpv uwsgi/nbhosting.service $(TESTBOX):/etc/systemd/system/
	ssh $(TESTBOX) systemctl restart nbhosting
	# tmp
	rsync -tpv jupyter/jupyter_notebook_config.py $(TESTBOX):/nbhosting-test/jupyter/flotbioinfo/
	rsync -rltpv --exclude pics jupyter/custom.* $(TESTBOX):/nbhosting-test/jupyter/flotbioinfo/custom/


