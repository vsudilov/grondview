from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from grondview.settings import PROJECT_ROOT
from imagequery.models import ImageHeader

import sys
import os

from grondview.settings import PROJECT_ROOT
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))

from lib import constants

from astLib import astCoords


class UserAstrphot(models.Model):
  jobid = models.CharField(max_length=30)
  logfile_path = models.CharField(max_length=50)
  image_path = models.CharField(max_length=50)
  user = models.ForeignKey(User)
