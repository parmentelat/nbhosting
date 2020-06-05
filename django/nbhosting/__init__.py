# ever since Ive been using db-backed models
# I keep on running into the infamous
# "AppRegistryNotReady: Apps aren't loaded yet"
# exception thrown by django at random stages
# including and most frustatingly when running
# setup.py and/or manage.py
#
# so I am taking the drastic step of removing *ANY* autoimport
# feature in here
