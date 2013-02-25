from __future__ import absolute_import

from grondview.celery import celery
from astLib import astCoords

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
def add(x, y):
    return x + y


@celery.task
def mul(x, y):
    return x * y


@celery.task
def xsum(numbers):
    return sum(numbers)

@celery.task
def makeImage(image):
  fname = image['PATH_PNG']
  d = pyfits.open(image['PATH_RAW'])[0].data
  astImages.saveBitmap(os.path.join(MEDIA_ROOT,fname),d,cutLevels=["smart", 99.5],size=300,colorMapName='gray')

  return None
