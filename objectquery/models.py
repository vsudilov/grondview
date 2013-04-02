from django.db import models
from django.db.models.query import QuerySet
from imagequery.models import ImageHeader
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
class AstroSourceQuerySet(QuerySet):
  def sourcePositionFilter(self,ra,dec,radius,units="arcseconds"):
    """
    Filters a queryset based on arclength. Returns a List of 
    database rows, therefore must be the last piece of a QuerySet chain.
    """
    radius *= constants.convert_arcmin_or_arcsec_to_degrees[units]

    results = []
    for i in self:
      distance = astCoords.calcAngSepDeg(i.RA,i.DEC,ra,dec)
      if distance <= radius:
        i.__setattr__("distance",distance)
        results.append(i)
    return results
class AstroSourceManager(models.Manager):
  def get_query_set(self):
    return AstroSourceQuerySet(self.model)
  def __getattr__(self, name):
    return getattr(self.get_query_set(), name)
  def get_by_natural_key(self, sourceID):
    return self.get(sourceID=sourceID)
#--------------------------------------------

class AstroSource(models.Model):
  '''
  Detected source
  '''
  def __unicode__(self):
    return "%s" % (self.sourceID) 
  
  #one object should have 7 image headers, regardless if they are 99% redundant
  imageheader = models.ManyToManyField(ImageHeader,related_name="%(app_label)s_%(class)s_related") 

  sourceID = models.CharField(max_length=30) #Unique source ID, GROND_HHMMSS.S+/-DDMMSS.S
  name = models.CharField(max_length=30,null=True) #Optional name to add to the source

  #No distinction between calib and zeropoint magnitudes,
  #as we should not report zeropoint mags in production
  RA = models.FloatField() #Object (not field) wcs
  DEC = models.FloatField()

  #-- Manager
  objects = AstroSourceManager()

  def natural_key(self):
    return (self.sourceID,)

class Photometry(models.Model):
  '''
  Photometric parameters
  '''

  def __unicode__(self):
    return '%s: %s-%s' % (self.astrosource,self.imageheader.OB,self.BAND)
  
  astrosource = models.ForeignKey(AstroSource)
  imageheader = models.ForeignKey('imagequery.ImageHeader',related_name="%(app_label)s_%(class)s_related")

  MAG_PSF = models.FloatField()
  MAG_PSF_ERR = models.FloatField()
  MAG_APP = models.FloatField()
  MAG_APP_ERR = models.FloatField()
  MAG_KRON = models.FloatField()
  MAG_KRON_ERR = models.FloatField()
  ELONGATION = models.FloatField()
  R_HALFLIGHT = models.FloatField()
  BAND = models.CharField(max_length=1)  


  
  
