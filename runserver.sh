#!/bin/bash

#compile js
./coffeecompile.sh

#Create stubdata, load it, sync it
python manage.py syncdb

#python manage.py loaddata fixtures/stubdata.json
python manage.py collectstatic --noinput

if [ ! -f .db_initialized ];
then
  echo "Populating the database since this seems to be the initial run"
  python manage.py populateDB && touch .db_initialized
fi

#Run dev server
#Change default bind address from loopback to 0.0.0.0 to be discoverable on the host machine
python manage.py runserver 0.0.0.0:8000
