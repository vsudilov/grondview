'''
Populates the grondviewdb database. 
'''

import os,sys
import pyfits
import re
from astLib import astCoords

from imagequery.models import ImageHeader,ImageProperties
from objectquery.models import AstroSource,Photometry
from grondview.settings import PROJECT_ROOT

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import resultfile
from lib import deg2sex

class GrondData:
  def __repr__(self):
    return self.path

  def __init__(self,path,**kwargs):
    self.args = kwargs
    self.path = path
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

  def _arclength(self,ra1,dec1,ra2,dec2):
    from math import cos, pi
    def cosd(degs):
      return cos(degs*pi/180)
    return (    (    (ra1-ra2)*cosd(  (dec1+dec2)/2.0  )  )**2 + (dec1-dec2)**2)**(1/2.)*60.*60.

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
      modelfields = ('PATH','NAXIS1', 'NAXIS2', 'RA', 'DEC', 'EXPTIME', 'MJD_OBS', 
                     'DATE_OBS', 'CRVAL1', 'CRVAL2', 'NGR', 'NINT', 'NIZ', 'NMD', 
                     'NTD', 'NTP', 'OBSEQNUM', 'OBSRUNID', 'TARGETID', 'FILTER', 'RON',
                     'GAIN', 'MJD_MID', 'OBSERR', 'NCOMBINE', 'NIMGS', 'TDP_MID', 
                     'INTERPSM', 'AIRMASS', 'IMGEXP','OBTYPEID')
      matched = dict( [(k,v) for k,v in fields.iteritems() if k in modelfields]  )
      return matched
    fields = dict([(k.replace('-','_'),self.header[k]) for k in self.header if k]) 
    fields = _match_db_fields(fields) #Need to remove the extraneous keys...Django blindly tries to copy all keys to models 
    fields['PATH'] = self.image
    try:
      result = ImageHeader.objects.get(PATH=fields['PATH']) 
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
      fields[k] = self.resultfile.header[translation[k]]
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
    previously_detected_sources = AstroSource.objects.all()
    self.old_sources = []
    for pds in previously_detected_sources:
      for source in all_sources:
        if self._arclength(pds.RA,pds.DEC,source['RA'],source['DEC']) <= self.args['match_tolerance']:
          #Even if this source already exists, this may be a new observation of it
          #Therefore, we need to check also the ImageHeader(s) of this source, and
          #Add this one in if it doesnt exist.
          sexRa,sexDec = deg2sex.main(pds.RA,pds.DEC)
          sourceID = 'GROND_J%s%s' % (sexRa,sexDec)
          this_source = AstroSource.objects.get(sourceID=sourceID)    
          ihs = [i.PATH for i in this_source.imageheader.all()]
          if self.imageheader.PATH not in ihs:
            this_source.imageheader.add(self.imageheader)
            this_source.save(force_update=True)
          self.old_sources.append(this_source)
          all_sources.remove(source)
    print "     (after removal of sources already in the database, %s new sources remain)" % len(all_sources)

    #Finally, make the Django models and save to DB
    self.new_sources = []
    for source in all_sources:
      fields = {}
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
    translation = {'MAG_PSF':'MAG_PSF',
                 'MAG_PSF_ERR':'MAG_PSF_ERR',
                 'MAG_APP':'MAG_APP',
                 'MAG_APP_ERR':'MAG_APP_ERR',
                 'MAG_KRON':'MAG_KRON',
                 'MAG_KRON_ERR':'MAG_KRON_ERR',
                 'ELONGATION':'ELONGATION',
                 'R_HALFLIGHT':'R_HALFLIGHT'}    
    for source in self.sources:
      matched = self.resultfile.getNearbyObjs(source.RA,source.DEC,limit=1)
      s = matched.keys()[0]
      if matched[s]['DISTANCE'] > self.args['match_tolerance']:
        continue
      fields = {}
      for k in translation:
        v = matched[s][translation[k]]
        try:
          fields[k] = float(v)
        except ValueError:
          fields[k] = -99
      fields['BAND'] = self.resultfile.header['BAND']
      fields['imageheader'] = self.imageheader
      fields['astrosource'] = source
      result = Photometry.objects.filter(astrosource__sourceID=source.sourceID).filter(imageheader__PATH=self.imageheader.PATH) 
      if result:
        fields['pk'] = result[0].pk
      self.photometry = Photometry(**fields)
      self.photometry.save()

def main(*args,**kwargs):
  DATADIR = args[0]
  FITS_REGEX = kwargs['fits_regex']
  for path, dirs, files in os.walk(DATADIR):
    for f in files:
      if re.search(FITS_REGEX,f):
        fullpath = os.path.abspath(path)
        f = GrondData(fullpath,**kwargs)
        print "Adding data in %s to db" % fullpath
        f.populateDB()
        break
  

if __name__=="__main__":
  main()
