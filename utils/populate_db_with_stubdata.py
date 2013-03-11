'''
Create JSON from stubdata for use with `manage.py loaddata`
vss
'''
import os
import sys
import pyfits
import json

from astLib import astCoords
from lib import resultfile
from lib.constants import convert_arcmin_or_arcsec_to_degrees

FIXTURES_DIR = os.path.join(os.path.dirname(__file__),'../fixtures/')
STUB_DIR =  os.path.join(os.path.dirname(__file__),'../stubdata/')
BANDS = 'grizJHK'
FITS = "%s_binned.fits"
RESULT = "%s.result"
MATCH_TOLERANCE = 0.3 #arcseconds tolerance to match sources between bands
REF_CATALOG = "r/r.result"

def writeJSON(data,OUTPUT_FILENAME="stubdata.json"):
  #Write the final JSON product to disk 
  if os.path.isfile(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME)):
    os.remove(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME))
    print "Removed previous %s" % OUTPUT_FILENAME
  with open(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME),'a') as fp:
    json.dump(data,fp,indent=1)
  print "Populated %s with info from %s" % (OUTPUT_FILENAME,STUB_DIR)


class Target:
  def __repr__(self):
    return self.path

  def __init__(self,path):
    self.path = os.path.abspath(path)
    self.ref_catalog = resultfile.ResultFile(os.path.join(path,REF_CATALOG))
    self.json = {}
    self.bands = BANDS
    self.json['imagequery'] = []
    self.json['objectquery'] = []
    self.images = {}
    self.headers = {}
    self.resultfiles = {}
    for band in self.bands:
      d = os.path.join(self.path,band)
      self.images[band] = os.path.join(d,FITS % band)
      hdulist = pyfits.open(self.images[band])
      self.headers[band] = hdulist[0].header
      self.resultfiles[band] = resultfile.ResultFile(os.path.join(d,RESULT % band))

  def _findPK(self,J,app):
    return len( [i for i in self.json[app] if i['model']==J['model'] ] )+1

  def _arclength(self,ra1,dec1,ra2,dec2):
    from math import cos, pi
    def cosd(degs):
      return cos(degs*pi/180)
    return (    (    (ra1-ra2)*cosd(  (dec1+dec2)/2.0  )  )**2 + (dec1-dec2)**2)**(1/2.)*60.*60.

  def make_ImageHeader(self):
    for band in self.bands:
      fields = {}
      J = {}
      J['model'] = 'imagequery.ImageHeader'
      J['pk'] = self._findPK(J,'imagequery')
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
      J['fields'] = fields
      self.json['imagequery'].append(J)

  def make_ImageProperties(self):
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
    for band in self.bands:
      fields = {}      
      J = {}
      J['model'] = 'imagequery.ImageProperties'
      J['pk'] = self._findPK(J,'imagequery')
      for k in translation:
        fields[k] = self.resultfiles[band].header[translation[k]]
      fields['imageheader'] = [ self.images[band] ] #Outer list needed for django-parser to lookup by natural key
      J['fields'] = fields
      self.json['imagequery'].append(J)

  def make_AstroSource(self):
    for obj in self.ref_catalog.objects:
      J = {}
      J['model'] = 'objectquery.AstroSource'
      J['pk'] = self._findPK(J,'objectquery')
      fields = {}
      fields['sourceID'] = '%s-%s' % (self.ref_catalog.header['TARGET'],obj['ObjID'])
      fields['RA'] = obj['RA']
      fields['DEC'] = obj['DEC']
      J['fields'] = fields
      self.json['objectquery'].append(J)

  def make_Photometry(self):
    translation = {'MAG_PSF':'MAG_PSF',
                 'MAG_PSF_ERR':'MAG_PSF_ERR',
                 'MAG_APP':'MAG_APP',
                 'MAG_APP_ERR':'MAG_APP_ERR',
                 'MAG_KRON':'MAG_KRON',
                 'MAG_KRON_ERR':'MAG_KRON_ERR',
                 'ELONGATION':'ELONGATION',
                 'R_HALFLIGHT':'R_HALFLIGHT'}    
    for band in self.bands:
      for source in self.resultfiles[band].objects:
        for ref_source in self.ref_catalog.objects:
          if self._arclength(ref_source['RA'],ref_source['DEC'],source['RA'],source['DEC']) <= MATCH_TOLERANCE:
            J = {}
            J['model'] = 'objectquery.Photometry'            
            J['pk'] = self._findPK(J,'objectquery')
            fields = {}      
            for k in translation:
              v = source[translation[k]]
              try:
                fields[k] = float(v)
              except ValueError:
                fields[k] = -99
            fields['imageheader'] = [ self.images[band] ]
            fields['astrosource'] = [ '%s-%s' % (self.ref_catalog.header['TARGET'],ref_source['ObjID']) ] 
            J['fields'] = fields
            self.json['objectquery'].append(J)
            break 


def main():

  targets = []
  json = []
  for directory in os.listdir(STUB_DIR):
    fullpath = os.path.join(STUB_DIR,directory)
    targets.append(Target(fullpath))

  [i.make_ImageHeader() for i in targets]
  [i.make_ImageProperties() for i in targets]
  [i.make_AstroSource() for i in targets]
  [i.make_Photometry() for i in targets]

  django_json = []  #Django json parser (for stubdata) requires a specific top level organization
  for t in targets:
    for app in ['imagequery','objectquery']:
      django_json.extend( t.json[app] )
  writeJSON(django_json)
  


if __name__ == "__main__":
  main()
