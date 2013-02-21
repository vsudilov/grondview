from __future__ import absolute_import

from grondview.celery import celery
from astLib import astCoords
from astLib import astImages
import pyfits
import os
from grondview.settings import MEDIA_ROOT
import sys



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
def makeImages(images):
  for i in images:
    fname = i['PATH_PNG']
    d = pyfits.open(i['PATH_RAW'])[0].data
    astImages.saveBitmap(os.path.join(MEDIA_ROOT,fname),d,cutLevels=["smart", 99.5],size=300,colorMapName='gray') 
  return None
