'''
Populates the grondviewdb database. 
'''

import os,sys
import pyfits
import re
import ConfigParser
import subprocess
import datetime
from astLib import astCoords
from astLib import astWCS

from imagequery.models import ImageHeader,ImageProperties
from objectquery.models import AstroSource,Photometry
from django.contrib.auth.models import User

from grondview.settings import PROJECT_ROOT
from grondview.settings import DATADIR

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import resultfile
from lib import deg2sex
from lib import constants

from math import cos, pi

class GrondData:
  def __repr__(self):
    return self.path

  def __init__(self,path,user,**kwargs):
    self.args = kwargs
    self.path = path
    self.user = user
    self.resultfile = None
    for f in os.listdir(path):
      if re.search(kwargs['fits_regex'],f):
        self.image = os.path.join(path,f)
      if re.search(kwargs['results_regex'],f): 
        self.resultfile = resultfile.ResultFile(os.path.join(path,f))
    if not self.resultfile:
      sys.exit("FATAL: No resultfiles found in [%s], yet the reduced image seems to exist." % self.path)
    hdulist = pyfits.open(self.image)
    self.header = hdulist[0].header

  def populateDB(self):
    self._make_ImageHeader()
    print "  --> ImageHeader done."
    self._make_ImageProperties()
    print "  --> ImageProperties done."
    self._make_AstroSource()
    print "  --> AstroSource done."
    self._make_Photometry()
    print "  --> Photometry done."

  def _make_ImageHeader(self):
    fields = {}
    def _match_db_fields(fields):
      #Match the FITS header keys with those defined in the database table
      modelfields = ('PATH','NAXIS1', 'NAXIS2', 'EXPTIME', 'MJD_OBS', 
                     'DATE_OBS', 'CRVAL1', 'CRVAL2', 'NGR', 'NINT', 'NIZ', 'NMD', 
                     'NTD', 'NTP', 'OBSEQNUM', 'OBSRUNID', 'TARGETID', 'FILTER', 'RON',
                     'GAIN', 'MJD_MID', 'OBSERR', 'NCOMBINE', 'NIMGS', 'TDP_MID', 
                     'INTERPSM', 'AIRMASS', 'IMGEXP','OBTYPEID')
      matched = dict( [(k,v) for k,v in fields.iteritems() if k in modelfields]  )
      return matched
    fields = dict([(k.replace('-','_'),self.header[k]) for k in self.header if k]) 
    fields = _match_db_fields(fields) #Need to remove the extraneous keys...Django blindly tries to copy all keys to models 
    fields['PATH'] = self.image
    fields['OBTYPEID'] = fields['OBTYPEID'].replace('min','m')
    fields['OB_CORR'] = self.header.get('OB_CORR','')
    wcs = astWCS.WCS(self.image)
    fields['RA'], fields['DEC'] = wcs.pix2wcs(self.header['NAXIS1']/2.0,self.header['NAXIS2']/2.0)
    fields['BOTTOMLEFT_RA'], fields['BOTTOMLEFT_DEC'] = wcs.pix2wcs(0,0)
    fields['TOPRIGHT_RA'], fields['TOPRIGHT_DEC'] = wcs.pix2wcs(self.header['NAXIS1'],self.header['NAXIS2'])
    try:
      result = ImageHeader.objects.get(
                                      TARGETID=fields['TARGETID'],
                                      OB_CORR=fields['OB_CORR'],
                                      OBSEQNUM=fields['OBSEQNUM'],
                                      OBSRUNID=fields['OBSRUNID'],
                                      FILTER=fields['FILTER'],
                                      )
      print "NOTE: This field already exists in the database. I will UPDATE the values for it instead of INSERT a new row"
      fields['pk'] = result.pk
    except ImageHeader.DoesNotExist:
      pass
    self.imageheader = ImageHeader(**fields)
    self.imageheader.save()

  def _make_ImageProperties(self):
    translation = {'LIMITING_MAG_3S_ZP':'LIMITING_MAG_3SIG_ZP',
                 'LIMITING_MAG_3S_CALIB':'LIMITING_MAG_3SIG_CALIB',
                 'SEEING':'MEAN_FWHM_ARCSEC',
                 'MEAN_AIRMASS':'MEAN_AIRMASS',
                 'ASTROMETRY_ACCURACY_RA':'ASTRO_SOLN_ACCURACY_RA',
                 'ASTROMETRY_ACCURACY_DEC':'ASTRO_SOLN_ACCURACY_DEC',
                 'KRON_CORRECTION':'KRON_CORRECTION',
                 'APP_SIZE':'APERTURE_SIZE_ARCSEC',
                 'CALIB_CHI2':'CALIB_CHI2',
                 'CALIB_RMS':'CALIB_RMS'}
    fields = {}      
    for k in translation:
      fields[k] = self.resultfile.header.get(translation[k],-99)
    fields['LIMITING_MAG_3S_ZP'] += constants.convert_to_AB[self.imageheader.FILTER]
    fields['LIMITING_MAG_3S_CALIB'] += constants.convert_to_AB[self.imageheader.FILTER]
    fields['imageheader'] = self.imageheader
    try:
      result = ImageHeader.objects.get(PATH=fields['imageheader'].PATH)
      fields['pk'] = result.pk
    except ImageHeader.DoesNotExist:
      pass
    self.imageproperties = ImageProperties(**fields)
    self.imageproperties.save()

  def _make_AstroSource(self):
    all_sources = self.resultfile.objects[:]
    print "     (detected %s sources in this resultfile)" % len(all_sources)
    #Compare the sources detected in this resultfile the database. If sourceID already exists, we shouldn't re-write it!
    self.old_sources = []
    sources_to_remove = []
    for source in all_sources:
      r = sorted(AstroSource.objects.positionFilter(source['RA'],source['DEC'],self.args['match_tolerance']),key=lambda k: k.distance)
      if r:
        #Even if this source already exists, this may be a new observation of it
        #Therefore, we need to check also the ImageHeader(s) of this source, and
        #Add this one in if it doesnt exist.
        this_source = r[0] 
        if self.imageheader not in this_source.imageheader.all():
          this_source.imageheader.add(self.imageheader)
          this_source.save()
        self.old_sources.append(this_source)
        sources_to_remove.append(source)
    all_sources = [i for i in all_sources if i not in sources_to_remove]
    print "     (after removal of sources already in the database, %s new sources remain)" % len(all_sources)

    #Finally, make the Django models and save to DB
    self.new_sources = []
    for source in all_sources:
      fields = {}
      fields['user'] = self.user
      fields['RA'] = source['RA']
      fields['DEC'] = source['DEC']
      sexRa,sexDec = deg2sex.main(source['RA'],source['DEC'])
      fields['sourceID'] = 'GROND_J%s%s' % (sexRa,sexDec)
      d = AstroSource(**fields)
      d.save()
      d.imageheader.add(self.imageheader)
      self.new_sources.append(d)
    [i.save() for i in self.new_sources]
    self.sources = []
    self.sources.extend(self.old_sources)
    self.sources.extend(self.new_sources)

  def _make_Photometry(self):   
    for source in self.sources:
      matched = self.resultfile.getNearbyObjs(source.RA,source.DEC,limit=1)
      s = matched.keys()[0]
      if matched[s]['DISTANCE'] > self.args['match_tolerance']:
        continue
      fields = {}
      fields['user'] = self.user
      fields['BAND'] = self.resultfile.header['BAND']
      fields['imageheader'] = self.imageheader
      fields['astrosource'] = source

      [fields.update( {k:None} ) for k in ['MAG_PSF','MAG_PSF_ERR','MAG_APP','MAG_APP_ERR']] #Default to null photometry
      fields['CALIB_SCHEME'] = self.resultfile.header['CATALOG_CALIB']
      #Set up magnitudes from resultfiles      
      if fields['BAND'] in constants.infrared:
        #If JHK, take MAG_APP=MAG_CALIB, point to downloaded 2MASS catalog
        try:
          fields['MAG_APP'] = matched[s]['MAG_CALIB']+constants.convert_to_AB[fields['BAND']]
          fields['MAG_APP_ERR'] = matched[s]['MAG_CALIB_ERR']
        except TypeError:
          pass #Default None is already set
        fields['CALIB_FILE'] = os.path.join(os.path.dirname(self.imageheader.PATH),'GROND_%s_OB_cat_2MASS.tsv' % fields['BAND'])
      else:
        #if griz, take either CALIB is sdss/user catalog, else take zeropoints
        if fields['CALIB_SCHEME'].lower() in ['sdss','user']:
          fields['MAG_PSF'] = matched[s]['MAG_CALIB']
          fields['MAG_PSF_ERR'] = matched[s]['MAG_CALIB_ERR']
          try:
            fields['MAG_APP'] = matched[s]['MAG_APP']+matched[s]['OFFSET_ALL']
            fields['MAG_APP_ERR'] = ( matched[s]['MAG_APP_ERR']**2 + matched[s]['OFFSET_ALL_ERR']**2 ) ** (1/2.)
          except TypeError: #In case of value=INDEF from iraf
            pass #default None is already set
          if fields['CALIB_SCHEME'].lower() == 'sdss':
            fields['CALIB_FILE'] = os.path.join(os.path.dirname(self.imageheader.PATH),'GROND_%s_OB_cat_SDSS.tsv' % fields['BAND'])
          else:
            iniFile = os.path.join(DATADIR,self.imageheader.TARGETID,self.imageheader.OB,'%sana.ini' % fields['BAND'])
            cp = ConfigParser.ConfigParser()
            cp.read(iniFile)
            fields['CALIB_FILE'] = os.path.join(DATADIR,self.imageheader.TARGETID,self.imageheader.OB,'calcat_%s' % os.path.basename(cp.get('task','calcat')))  
        else:
          [fields.update( {k:matched[s][k]} ) for k in ['MAG_PSF','MAG_PSF_ERR','MAG_APP','MAG_APP_ERR']]
          fields['CALIB_SCHEME'] = 'ZP' #Overwrite 'USNO' calib scheme, as we never will report photometry against USNO
          fields['CALIB_FILE'] = None

      result = Photometry.objects.filter(astrosource__sourceID=source.sourceID).filter(imageheader__PATH=self.imageheader.PATH) 
      if result:
        fields['pk'] = result[0].pk
      self.photometry = Photometry(**fields)
      self.photometry.save()

def getPipelineUser():
  try:
    user = User.objects.get(username='pipeline')
  except User.DoesNotExist:
    print "Creating user 'pipeline' since it does not yet exist. All of the automatically analyzed data will be attributed to this account"
    user = User.objects.create_user(username='pipeline',email=None,password='.5arcsec')
    user.is_staff = False
    user.is_superuser = False
    user.save()
  return user

def checkLocks():
  lockfile = os.path.join(PROJECT_ROOT,'populateDB.lock')
  if os.path.isfile(lockfile):
    sys.exit('Only one instance of `manage.py populateDB` should run at a time:\nEXITING.')
  with open(lockfile,'w') as f:
    f.write(str(os.getpid()))

def main(*args,**kwargs):
  checkLocks()
  starttime = datetime.datetime.now()
  DATADIR = args[0]
  FITS_REGEX = kwargs['fits_regex']
  user = getPipelineUser()
  for path, dirs, files in os.walk(DATADIR):
    for f in files:
      if re.search(FITS_REGEX,f):
        fullpath = os.path.abspath(path)
        if kwargs['only_recent']:
          mtime = os.path.getmtime(fullpath) #Get the modifcation time, in UNIX time
          date = datetime.datetime.fromtimestamp(mtime) #Store in a more easily manipulted datatime.date object
          if date <= starttime-datetime.timedelta(minutes=int(kwargs['only_recent'])):
            break
        f = GrondData(fullpath,user,**kwargs)
        print "Adding data in %s to db" % fullpath
        f.populateDB()
        break

if __name__=="__main__":
    main()
