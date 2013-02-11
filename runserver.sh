#!/bin/bash

#Change default bind address from loopback to 0.0.0.0 to be discoverable on the host machine
python manage.py runserver 0.0.0.0:8000
