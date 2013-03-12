from django.db import models
from django.db.models.query import QuerySet
import os
import sys

from grondview.settings import PROJECT_ROOT
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))

from lib import constants

from astLib import astCoords

#--------------------------------------------
#Clever trick to override QuerySets, enabling
#chaining of custom queries:
#Enables model.objects.positionFilter()
#as well as model.objects.filter(FILTER__in=bands).positionFilter(ra,dec,radius)
#http://zmsmith.com/2010/04/using-custom-django-querysets/
class ImageHeaderQuerySet(QuerySet):
  def imagePositionFilter(self,ra,dec,radius,units="arcminutes"):
    """
    Filters a queryset based on arclength. Returns a List of 
    database rows, therefore must be the last piece of a QuerySet chain.
    """
    radius *= constants.convert_arcmin_or_arcsec_to_degrees[units]

    results = []
    for i in self:
      if astCoords.calcAngSepDeg(i.CRVAL1,i.CRVAL2,ra,dec) <= radius:
        results.append(i)
    return results
class ImageHeaderManager(models.Manager):
  def get_query_set(self):
    return ImageHeaderQuerySet(self.model)

  def __getattr__(self, name):
    return getattr(self.get_query_set(), name)

  def get_by_natural_key(self, PATH):
    return self.get(PATH=PATH)
#--------------------------------------------


class ImageHeader(models.Model):
  """
  Stores FITS header info, along with path to that image
  """
  def __unicode__(self):
    return "%s" % (self.PATH)

  #-- Fields
  PATH = models.CharField(max_length=80)
  NAXIS1 = models.IntegerField()
  NAXIS2 = models.IntegerField()
  RA = models.FloatField() #Telescope pointing
  DEC = models.FloatField()
  EXPTIME = models.FloatField()
  MJD_OBS = models.FloatField()
  DATE_OBS = models.CharField(max_length=30)
  CRVAL1 = models.FloatField() #Center of field (astrometry)
  CRVAL2 = models.FloatField()
  NGR = models.IntegerField()
  NINT = models.IntegerField()
  NIZ = models.IntegerField()
  NMD = models.IntegerField()
  NTD = models.IntegerField()
  NTP = models.IntegerField()
  OBSEQNUM = models.IntegerField()
  OBSRUNID = models.IntegerField()
  TARGETID = models.CharField(max_length=40)
  FILTER = models.CharField(max_length=1)
  RON = models.FloatField()
  GAIN = models.FloatField()
  MJD_MID = models.FloatField()
  OBSERR = models.FloatField()
  NCOMBINE = models.IntegerField()
  NIMGS = models.IntegerField()
  TDP_MID = models.FloatField()
  INTERPSM = models.FloatField()
  AIRMASS = models.FloatField()
  IMGEXP = models.FloatField()

  def OB(self):
    return "OB%s_%s" % (self.OBSRUNID,self.OBSEQNUM)

  #-- Manager
  objects = ImageHeaderManager()

  def natural_key(self):
    return (self.PATH,) 
  
class ImageProperties(models.Model):
  '''
  Stores field properties derived from the analysis of the image
  '''
  imageheader = models.OneToOneField(ImageHeader)
  
  LIMITING_MAG_3S_ZP = models.FloatField()
  LIMITING_MAG_3S_CALIB = models.FloatField()
  SEEING = models.FloatField() #In arcseconds
  MEAN_AIRMASS = models.FloatField() #The FITS header only records airmass at start
  ASTROMETRY_ACCURACY_RA = models.FloatField()
  ASTROMETRY_ACCURACY_DEC = models.FloatField()
  KRON_CORRECTION = models.FloatField()
  APP_SIZE = models.FloatField() #In arcseconds
  CALIB_CHI2 = models.FloatField()
  CALIB_RMS = models.FloatField()

  #-- Manager
  objects = ImageHeaderManager()

  def __unicode__(self):
    return "%s-%s ImageProperties" % (self.imageheader.PATH,self.imageheader.FILTER)

class Field(models.Model):

  imageheader = models.ManyToManyField(ImageHeader,related_name="%(app_label)s_%(class)s_related")
  astrosource = models.ManyToManyField('objectquery.AstroSource')

  TARGETID = models.CharField(max_length=40)
  OB = models.CharField(max_length=10)

  def __unicode__(self):
    return "%s:%s" % (self.TARGETID,self.OB)

  def natural_key(self):
    return (self.TARGETID,OB) 
  

