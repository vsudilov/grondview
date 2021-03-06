from __future__ import absolute_import

from celery import current_task
from grondview.celery import celery
from astLib import astWCS

import pyfits
import os
import sys
import time
import logging

from grondview.settings import MEDIA_ROOT
from grondview.settings import PROJECT_ROOT

from forcedetect.models import UserTask_photometry

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import img_scale
from lib import astImages
from lib import constants
from lib import photometry as phot

from stsci.numdisplay import zscale


@celery.task
def makeImage(ImageHeaderInstance,fname,clipSize,ra,dec,units='arcseconds', **kwargs):
  d = pyfits.open(ImageHeaderInstance.PATH)[0].data
  cutout = {'data':d}
  scale=zscale.zscale(d)
  if clipSize:
    wcs = astWCS.WCS(ImageHeaderInstance.PATH)  
    clipSizeDeg = clipSize * constants.convert_arcmin_or_arcsec_to_degrees[units]
    cutout = astImages.clipImageSectionWCS(d, wcs, ra, dec, clipSizeDeg, returnWCS = False)
  else:
    clipSizeDeg = ImageHeaderInstance.TOPRIGHT_DEC-ImageHeaderInstance.BOTTOMLEFT_DEC
  caption = ImageHeaderInstance.FILTER
  ImageHeaderInstance.fname = fname
  try:
    astImages.saveBitmap(
      os.path.join(MEDIA_ROOT,fname),
      cutout['data'],
      cutLevels=["smart", 99.5],
      size=200,
      colorMapName='gray',
      caption=caption,
      clipSizeDeg=clipSizeDeg,
      scale=scale,
      )
  except:
    pass #Fail silently; rendering will recover
  return ImageHeaderInstance

@celery.task
def photometry(iniFile,targetid, OB, objwcs, **kwargs):
  request=current_task.request
  jobid = request.id
  if not os.path.isdir(os.path.join(MEDIA_ROOT,jobid)):
    os.mkdir(os.path.join(MEDIA_ROOT,jobid))
  
  logfmt = '%(levelname)s: (%(asctime)s) %(message)s'
  datefmt= '%I:%M:%S %p'
  formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
  logger = logging.getLogger('photometry')
  logging.root.setLevel(logging.DEBUG)
  fh = logging.FileHandler(filename=os.path.join(MEDIA_ROOT,jobid,'logfile'),mode='a') #file handler
  fh.setFormatter(formatter)
  logger.addHandler(fh)
  if not os.path.isfile(iniFile):
    logger.critical('Unable to locate the ini file!')
  try:
    results = phot.main(iniFile, targetid, OB, logger, objwcs, jobid)
  except:
    logger.critical('Some unknown error has occured')
    raise
  results.update({'ownership':kwargs['user']})
  return results
