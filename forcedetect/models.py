from django.db import models
from grondview.settings import PROJECT_ROOT
from imagequery.models import ImageHeader

import sys
import os
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import deg2sex

class UserDetection(models.Model):
  username = models.CharField(max_length=40)
  RA = models.FloatField()
  DEC = models.FloatField()
  imageheader = models.ForeignKey('imagequery.ImageHeader',related_name="%(app_label)s_%(class)s_related")

  #Unfortunately can't subclass models.Photometry, since it would require the same ForeignKey
  #schemes, and we want this table to be independent of the other tables  
  MAG_PSF = models.FloatField()
  MAG_PSF_ERR = models.FloatField()
  MAG_APP = models.FloatField()
  MAG_APP_ERR = models.FloatField()
  MAG_KRON = models.FloatField()
  MAG_KRON_ERR = models.FloatField()
  MAG_CALIB = models.FloatField()
  MAG_CALIB_ERR = models.FloatField()
  ELONGATION = models.FloatField()
  R_HALFLIGHT = models.FloatField()


  def __unicode__(self):
    return "Force detect: %s: %s,%s" % (self.imageheader,self.RA,self.DEC)
