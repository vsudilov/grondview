grondview
=========

assumes a `vagrant up` precise64.box environment. Packages from apt+pypi. iraf (400MB download) installed from precompiled tar.gz

nginx/uwsgi up by default. Kill these if you want to run the devel server.

Manually add data to the database with `manage.py populateDB ~/path/to/data/`. 10x10 binned data are provided in stubdata/ for visualizatinon, although of course no analysis can be done on them.

run `./runserver.sh` to start the development server.

connect to http://localhost:8000 on host machine.
