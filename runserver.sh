#!/bin/bash

#compile js
./coffeecompile.sh

#Create stubdata, load it, sync it
python manage.py syncdb
python utils/populate_db_with_stubdata.py
python manage.py loaddata fixtures/stubdata.json
python manage.py collectstatic --noinput

#Run dev server
#Change default bind address from loopback to 0.0.0.0 to be discoverable on the host machine
python manage.py runserver 0.0.0.0:8000
