'''
Create JSON from stubdata for use with `manage.py loaddata`
vss
'''
import os
import sys
import pyfits
import json

def main(OUTPUT_DIR='../fixtures/',INPUT_DIR='../stubdata/'):
  for f in os.listdir(INPUT_DIR):
    hdr = pyfits.open(f)



if __name__ == "__main__":
  main()



#import pyraf

#bands = 'grizJHK'
#for band in bands:
#  pyraf.iraf.blkavg(input='GROND_%s_OB_ana.fits' % band,output='%s_binned.fits' % band, b1=10,b2=10)


#class image_header(models.Model):
#  PATH = models.TextField()
#  NAXIS1 = models.IntegerField()
#  NAXIS2 = models.IntegerField()
#  RA2000 = models.FloatField()
#  DEC2000 = models.FloatField()
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

