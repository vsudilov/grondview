from __future__ import absolute_import

from grondview.celery import celery
from astLib import astWCS

import matplotlib
from matplotlib import pyplot as plt
import pyfits
import os
import sys

from grondview.settings import MEDIA_ROOT
from grondview.settings import PROJECT_ROOT

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import img_scale
from lib import astImages

@celery.task
def makeImage(ImageHeaderInstance,fname,clipSizeDeg,ra,dec):
  d = pyfits.open(ImageHeaderInstance.PATH)[0].data
  wcs = astWCS.WCS(ImageHeaderInstance.PATH)  
  cutout = astImages.clipImageSectionWCS(d, wcs, ra, dec, clipSizeDeg, returnWCS = False)
  astImages.saveBitmap(os.path.join(MEDIA_ROOT,fname),cutout['data'],cutLevels=["smart", 99.5],size=300,colorMapName='gray')
  return None
