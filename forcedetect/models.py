from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from grondview.settings import PROJECT_ROOT

import sys
import os

from grondview.settings import PROJECT_ROOT
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))

from lib import constants

from astLib import astCoords

#This should eventually be done with celery/redis !
class UserTask_photometry(models.Model):
  user = models.ForeignKey(User)
  jobid = models.CharField(max_length=40)
  sourceID = models.CharField(max_length=35)
  band = models.CharField(max_length=1)
  OB = models.CharField(max_length=10)
  targetID = models.CharField(max_length=40)
  logfile_line_number = models.IntegerField()

  def __unicode__(self):
    return self.jobid
