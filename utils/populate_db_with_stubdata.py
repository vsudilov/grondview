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
SOURCES = []
MATCH_TOLERANCE = 0.3 #arcseconds tolerance to match sources between bands

def writeJSON(data,OUTPUT_FILENAME="stubdata.json"):
  #Write the final JSON product to disk 
  if os.path.isfile(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME)):
    os.remove(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME))
    print "Removed previous %s" % OUTPUT_FILENAME
  with open(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME),'a') as fp:
    json.dump(data,fp,indent=1)
  print "Populated %s with info from %s" % (OUTPUT_FILENAME,STUB_DIR)


def pop_ImageProperties(rf,pk,D):
  fields = {}
  fields['imageheader'] = [ D['fields']['PATH'] ] #OneToOneField, with natural key
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
  for k in translation:
    fields[k] = rf.header[translation[k]]
  D = {"model":"imagequery.ImageProperties","fields":fields,'pk':pk}
  return D



def pop_AstroSource(source,pk,D):
  fields = {}
  #Setup the ManyToManyField relationship (one object has 7 images)
  #Bit of a cheat here, as we know what the stubdata filenames are
  p = D['fields']['PATH']
  b = D['fields']['FILTER']
  fields['imageheader'] = [[p.replace('%s_binned.fits' % b,'%s_binned.fits' % band)] for band in BANDS] 
  translation = {'RA':'RA',
                 'DEC':'DEC',
                 'MAG_PSF':'MAG_PSF',
                 'MAG_PSF_ERR':'MAG_PSF_ERR',
                 'MAG_APP':'MAG_APP',
                 'MAG_APP_ERR':'MAG_APP_ERR',
                 'MAG_KRON':'MAG_KRON',
                 'MAG_KRON_ERR':'MAG_KRON_ERR',
                 'ELONGATION':'ELONGATION',
                 'R_HALFLIGHT':'R_HALFLIGHT',}
  for k in translation:
    v = source[translation[k]]
    try:
      float(v)
      fields[k] = v
    except ValueError:
      fields[k] = -99
  radius=MATCH_TOLERANCE*convert_arcmin_or_arcsec_to_degrees['arcseconds']
  for src in SOURCES:
    if astCoords.calcAngSepDeg(source['RA'],source['DEC'],src['RA'],src['DEC']) <= radius:
      fields['sourceID'] = src['sourceID']
      break
  if not fields.has_key('sourceID'):
    fields['sourceID'] = '%s-%s' % (D['fields']['TARGETID'],source['ObjID'])
    SOURCES.append(fields)
  D = {"model":"objectquery.AstroSource","fields":fields,'pk':pk}
  return D
  


def pop_ImageHeader(hdr,pk,fits):
  def match_db_fields(fields):
    #Match the FITS header keys with those defined in the database table
    modelfields = ('PATH','NAXIS1', 'NAXIS2', 'RA', 'DEC', 'EXPTIME', 'MJD_OBS', 
                   'DATE_OBS', 'CRVAL1', 'CRVAL2', 'NGR', 'NINT', 'NIZ', 'NMD', 
                   'NTD', 'NTP', 'OBSEQNUM', 'OBSRUNID', 'TARGETID', 'FILTER', 'RON',
                   'GAIN', 'MJD_MID', 'OBSERR', 'NCOMBINE', 'NIMGS', 'TDP_MID', 
                   'INTERPSM', 'AIRMASS', 'IMGEXP')
    matched = dict( [(k,v) for k,v in fields.iteritems() if k in modelfields]  )
    return matched

  fields = dict([(k.replace('-','_'),hdr[k]) for k in hdr if k]) 
  fields = match_db_fields(fields) #Need to remove the extraneous keys...Django blindly tries to copy all keys to models
  fields['PATH'] = os.path.abspath(fits)
  D = {"model":"imagequery.ImageHeader","fields":fields,'pk':pk}
  return D



def populate_json(json,hdr,rf,fits,result):
  pk = len(json['imagequery'])/2+1
  D = pop_ImageHeader(hdr,pk,fits)
  json['imagequery'].append(D)
  json['imagequery'].append(pop_ImageProperties(rf,pk,D))
  
  for source in rf.objects:
    pk = max(len(json['objectquery']),1)  
    json['objectquery'].append(pop_AstroSource(source,pk,D))
  
  return json


def main():
  json = {}
  json['imagequery'] = []
  json['objectquery'] = []
  for directory in os.listdir(STUB_DIR):
    for band in BANDS:
      fullpath = os.path.join(STUB_DIR,directory)
      fits = os.path.join(fullpath,FITS % band)
      result = os.path.join(fullpath,RESULT % band)

      hdulist = pyfits.open(fits)
      hdr = hdulist[0].header
      rf = resultfile.ResultFile(result)      
      json = populate_json(json,hdr,rf,fits,result)

      

  django_json = []  #Django json parser (for stubdata) requires a specific top level organization
  for k in json:
    django_json.extend( json[k] )
  writeJSON(django_json)
  


if __name__ == "__main__":
  main()

