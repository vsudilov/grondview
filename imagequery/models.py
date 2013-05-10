from django.db import models
from django.db.models.query import QuerySet
from django.db.models import F
import os
import sys
import uuid

from grondview.settings import PROJECT_ROOT
from grondview.settings import DEBUG
from grondview import tasks
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
  def positionFilter(self,ra,dec,radius,units="arcminutes"):
    """
    Filters a queryset based on arclength. Returns a List of 
    database rows, therefore must be the last piece of a QuerySet chain.
    """
    radius *= constants.convert_arcmin_or_arcsec_to_degrees[units]

    results = []
    for i in self:
      distance = astCoords.calcAngSepDeg(i.CRVAL1,i.CRVAL2,ra,dec)
      if distance <= radius:
        i.__setattr__("distance",distance)
        results.append(i)
    return results

  def getBestImages(self,ra,dec,clipSize=10,seeing_limit=2.0,
                    makeImages=True,forceOB=None,units='arcseconds',
                    forceTarget=None,async=False): 
    '''  
    Find imageheaders that will be plotted. Find the "best", nominalOB, which has the following criteria:
    1. most filters
    2. depth (30m,20m,10m,8m,4m)
    3. seeing <= seeing_limit
    Returns a list of imageheader objects, sorted by band
    '''
    def doTask(imageheaders):
      imageheaders = sorted(imageheaders,key = lambda k: constants.band_sequence[k.FILTER])
      #Create image cut-outs
      #if DEBUG:
      #clipSize*=10 #For stubdata only!
      for hdr in imageheaders:
        fname = '%s.png' % uuid.uuid4()
        hdr.fname = fname #This attribute links the filename to the <img src=''> tag
        if async:
          t = tasks.makeImage.delay(hdr,fname,clipSize,ra,dec,units=units)
          hdr.jobid = t.id
        else:
          tasks.makeImage(hdr,fname,clipSize,ra,dec,units=units)
    
    if forceOB: #Bit sloppy code here!
      if forceTarget:
        imageheaders = self.filter(OB=forceOB).filter(TARGETID=forceTarget).positionFilter(ra,dec,radius=10)
      else:
        imageheaders = self.filter(OB=forceOB).positionFilter(ra,dec,radius=10) 
      if makeImages:
        doTask(imageheaders)
      return imageheaders  
    
    candidateOBs = {}
    results = self.filter(imageproperties__SEEING__lte=seeing_limit).positionFilter(ra,dec,radius=10,units='arcminutes')
    if not results:
      return None
    for r in results:
      try:
        candidateOBs[r.TARGETID+r.OB].append(r)
      except KeyError:
        candidateOBs[r.TARGETID+r.OB] = [r]
    max_filters = max( [len(i) for i in candidateOBs.values()] )
    candidateOBs = [i for i in candidateOBs.values() if len(i)==max_filters]
    imageheaders = sorted(candidateOBs, key = lambda k: constants.obtypes_sequence[k[0].OBTYPEID])[0]
    if makeImages:
      doTask()
    return imageheaders



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
  OBTYPEID = models.CharField(max_length=10)
  OB = models.CharField(max_length=10,null=True)


  def save(self, *args, **kwargs):
    self.OB="OB%s_%s" % ( self.OBSRUNID, self.OBSEQNUM )
    super(ImageHeader, self).save(*args, **kwargs) # Call the "real" save() method.

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
  

