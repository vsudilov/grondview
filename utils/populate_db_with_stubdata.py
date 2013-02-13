'''
Create JSON from stubdata for use with `manage.py loaddata`
vss
'''
import os
import sys
import pyfits
import json

FIXTURES_DIR = os.path.join(os.path.dirname(__file__),'../fixtures/')
STUB_DIR =  os.path.join(os.path.dirname(__file__),'../stubdata/')



def writeJSON(data,OUTPUT_FILENAME="stubdata.json"):
  #Write the final JSON product to disk 
  if os.path.isfile(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME)):
    os.remove(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME))
    print "Removed previous %s" % OUTPUT_FILENAME
  with open(os.path.join(FIXTURES_DIR,OUTPUT_FILENAME),'a') as fp:
    json.dump(data,fp,indent=1)
  print "Populated %s with info from %s" % (OUTPUT_FILENAME,STUB_DIR)


def match_db_fields(fields):
  #Match the FITS header keys with those defined in the database table
  modelfields = ('PATH','NAXIS1', 'NAXIS2', 'RA', 'DEC', 'EXPTIME', 'MJD_OBS', 
                 'DATE_OBS', 'CRVAL1', 'CRVAL2', 'NGR', 'NINT', 'NIZ', 'NMD', 
                 'NTD', 'NTP', 'OBSEQNUM', 'OBSRUNID', 'TARGETID', 'FILTER', 'RON',
                 'GAIN', 'MJD_MID', 'OBSERR', 'NCOMBINE', 'NIMGS', 'TDP_MID', 
                 'INTERPSM', 'AIRMASS', 'IMGEXP')
  matched = dict( [(k,v) for k,v in fields.iteritems() if k in modelfields]  )
  return matched

  

def main():
  json = {}
  json['imagequery'] = []
  json['objectquery'] = []
  i,j = 0,0 #Counters needed for required 'pk' field
  for f in os.listdir(STUB_DIR):
    if f.endswith('.fits'):
      i+=1 

      hdulist = pyfits.open(os.path.join(STUB_DIR,f))
      hdr = hdulist[0].header

      fields = dict([(k.replace('-','_'),hdr[k]) for k in hdr if k]) #pyfits does not make its dict transparent. Easier to just build a new one.
      fields = match_db_fields(fields) #Need to remove the extraneous keys...Django blindly tries to copy all keys to models
      fields['PATH'] = os.path.join(os.path.abspath('.'),os.path.join(STUB_DIR,f))
      json['imagequery'].append({"model":"imagequery.ImageHeader","fields":fields,'pk':i})
    elif f.endswith('.result'):      
      pass
      j+=1

  django_json = []  #Django json parser requires a specific top level organization
  for k in json:
    django_json.extend( json[k] )
  writeJSON(django_json)
  


if __name__ == "__main__":
  main()


#{
#    "pk": 1,
#    "model": "store.book",
#    "fields": {
#        "name": "Mostly Harmless",
#        "author": 42
#    }
#}


#import pyraf

#bands = 'grizJHK'
#for band in bands: #10x10 binning for stubdata, ie useless for science
#  pyraf.iraf.blkavg(input='GROND_%s_OB_ana.fits' % band,output='%s_binned.fits' % band, b1=10,b2=10)


#class ImageHeader(models.Model):
#  PATH = models.TextField()
#  NAXIS1 = models.IntegerField()
#  NAXIS2 = models.IntegerField()
#  RA = models.FloatField()
#  DEC = models.FloatField()
#  EXPTIME = models.FloatField()
#  MJD_OBS = models.FloatField()
#  DATE_OBS = models.TextField()
#  CRVAL1 = models.FloatField()
#  CRVAL2 = models.FloatField()
#  NGR = models.IntegerField()
#  NINT = models.IntegerField()
#  NIZ = models.IntegerField()
#  NMD = models.IntegerField()
#  NTD = models.IntegerField()
#  NTP = models.IntegerField()
#  OBSEQNUM = models.IntegerField()
#  OBSRUNID = models.IntegerField()
#  TARGETID = models.CharField(max_length=40)
#  FILTER = models.CharField(max_length=1)
#  RON = models.FloatField()
#  GAIN = models.FloatField()
#  MJD_MID = models.FloatField()
#  OBSERR = models.FloatField()
#  NCOMBINE = models.IntegerField()
#  NIMGS = models.IntegerField()
#  TDP_MID = models.FloatField()
#  INTERPSM = models.FloatField()
#  AIRMASS = models.FloatField()
#  IMGEXP = models.FloatField()

