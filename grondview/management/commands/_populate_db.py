'''
Populates the grondviewdb database. 
'''

import os,sys
import pyfits
import json
from astLib import astCoords

from imagequery.models import ImageHeader,ImageProperties,Field
from objectquery.models import AstroSource,Photometry
from grondview.settings import PROJECT_ROOT

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import resultfile

FITS = "%s_binned.fits"
RESULT = "%s.result"
DATADIR = "/home/vagrant/grondview/stubdata"
MATCH_TOLERANCE = 0.3
BANDS = 'grizJHK'

class GrondData:
  def __repr__(self):
    return self.path

  def __init__(self,path):
    self.path = path
    self.bands = BANDS
    self.images = {}
    self.headers = {}
    self.resultfiles = {}
    for band in self.bands:
      d = os.path.join(self.path,band)
      self.images[band] = os.path.join(d,FITS % band)
      hdulist = pyfits.open(self.images[band])
      self.headers[band] = hdulist[0].header
      self.resultfiles[band] = resultfile.ResultFile(os.path.join(d,RESULT % band))

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
    self._make_Field()
    print "  --> Field done."

  def _make_ImageHeader(self):
    self.imageheaders = {}
    for band in self.bands:
      fields = {}
      def _match_db_fields(fields):
        #Match the FITS header keys with those defined in the database table
        modelfields = ('PATH','NAXIS1', 'NAXIS2', 'RA', 'DEC', 'EXPTIME', 'MJD_OBS', 
                       'DATE_OBS', 'CRVAL1', 'CRVAL2', 'NGR', 'NINT', 'NIZ', 'NMD', 
                       'NTD', 'NTP', 'OBSEQNUM', 'OBSRUNID', 'TARGETID', 'FILTER', 'RON',
                       'GAIN', 'MJD_MID', 'OBSERR', 'NCOMBINE', 'NIMGS', 'TDP_MID', 
                       'INTERPSM', 'AIRMASS', 'IMGEXP')
        matched = dict( [(k,v) for k,v in fields.iteritems() if k in modelfields]  )
        return matched
      fields = dict([(k.replace('-','_'),self.headers[band][k]) for k in self.headers[band] if k]) 
      fields = _match_db_fields(fields) #Need to remove the extraneous keys...Django blindly tries to copy all keys to models 
      fields['PATH'] = self.images[band]
      self.imageheaders[band] = ImageHeader(**fields)
      self.imageheaders[band].save()

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
    self.imageproperties = {}
    for band in self.bands:
      fields = {}      
      for k in translation:
        fields[k] = self.resultfiles[band].header[translation[k]]
      fields['imageheader'] = self.imageheaders[band]
      self.imageproperties[band] = ImageProperties(**fields)
      self.imageproperties[band].save()

  def _make_AstroSource(self):
    #Find the union of unique sources (based on position) among all bands
    all_sources = []
    for band in self.bands:
      for current_source in self.resultfiles[band].objects:
        known = False
        for source in all_sources:
          if self._arclength(current_source['RA'],current_source['DEC'],source['RA'],source['DEC']) <= MATCH_TOLERANCE:
            known = True
            break
        if not known:
          current_source.update(ObjID=len(all_sources)+1)
          all_sources.append(current_source)
    
    print "     (detected %s unique sources among all bands)" % len(all_sources)
    #Compare the sources detected in this OB with all previous OBs. If sourceID already exists, we shouldn't re-write it!
    previously_detected_sources = AstroSource.objects.filter(imageheader__TARGETID__exact=self.imageheaders['r'].TARGETID)
    for pds in previously_detected_sources:
      for source in all_sources:
        if self._arclength(pds.RA,pds.DEC,source['RA'],source['DEC']) <= MATCH_TOLERANCE:        
          all_sources.remove(source)
    print "     (after removal of sources from previous OBs of the same field, %s unique sources remain)" % len(all_sources)
    #Finally, make the Django models and save to DB
    self.sources = []
    for source in all_sources:
      fields = {}
      fields['RA'] = source['RA']
      fields['DEC'] = source['DEC']
      fields['sourceID'] = '%s-%s' % (self.imageheaders['r'].TARGETID,source['ObjID'])
      d = AstroSource(**fields)
      d.save()
      for h in self.imageheaders.values():
        d.imageheader.add(h)
      self.sources.append(d)
    [i.save() for i in self.sources]

  def _make_Photometry(self):
    translation = {'MAG_PSF':'MAG_PSF',
                 'MAG_PSF_ERR':'MAG_PSF_ERR',
                 'MAG_APP':'MAG_APP',
                 'MAG_APP_ERR':'MAG_APP_ERR',
                 'MAG_KRON':'MAG_KRON',
                 'MAG_KRON_ERR':'MAG_KRON_ERR',
                 'ELONGATION':'ELONGATION',
                 'R_HALFLIGHT':'R_HALFLIGHT'}    
    self.photometry = {}
    for band in self.bands:
      for source in self.sources:
        matched = self.resultfiles[band].getNearbyObjs(source.RA,source.DEC,limit=1)
        s = matched.keys()[0]
        if matched[s]['DISTANCE'] > MATCH_TOLERANCE:
          continue
        fields = {}
        for k in translation:
          v = matched[s][translation[k]]
          try:
            fields[k] = float(v)
          except ValueError:
            fields[k] = -99
        fields['BAND'] = band
        fields['imageheader'] = self.imageheaders[band]
        fields['astrosource'] = source
        self.photometry[band] = Photometry(**fields)
        self.photometry[band].save()

  def _make_Field(self):
    fields = {}
    fields['TARGETID'] = self.imageheaders['r'].TARGETID
    fields['OB'] = self.imageheaders['r'].OB()
    self.field = Field(**fields)
    self.field.save()
    for h in self.imageheaders.values():
      self.field.imageheader.add(h)
    for s in self.sources:
      self.field.astrosource.add(s)
    self.field.save()

def main():
  for directory in os.listdir(DATADIR):
    fullpath = os.path.abspath(os.path.join(DATADIR,directory))
    f = GrondData(fullpath)
    print "Adding data in %s to db" % fullpath
    f.populateDB()
  

if __name__=="__main__":
  main()
