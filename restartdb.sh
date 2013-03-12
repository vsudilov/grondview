#!/bin/bash

sudo su postgres -c "dropdb grondviewdb"
sudo puppet apply manifests/precise64.pp --modulepath manifests/modules
rm .db_initialized
python manage.py syncdb

