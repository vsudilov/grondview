from __future__ import absolute_import

from grondview.celery import celery
from astLib import astCoords
from astLib import astImages
import pyfits
import uuid
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
def makeImages(queryrows):
#  images = []
#  for i in queryrows:
#    image = i.__dict__
#    image['DATE_OBS'] = image['DATE_OBS'].replace('T',' ')
#    d = pyfits.open(i.PATH)[0].data
#    unique_filename = uuid.uuid4()
#    fname = 'CELERY_%s.png' % unique_filename
#    image['PATH_PNG'] = fname
#    image['PATH_RAW'] = i.PATH
#    astImages.saveBitmap(os.path.join(MEDIA_ROOT,fname),d,cutLevels=["smart", 99.5],size=300,colorMapName='gray')
#    images.append('CELERY_%s' % image)  
#  return images
  with open('/home/vagrant/grondview/test','w') as f:
    f.write(os.getcwd())
  import matplotlib
  from matplotlib import pylab
  images = None
#  fp = open('/home/vagrant/grondview/test','a')
#  fp.write('\n'.join(sys.path))
#  fp.write('\n--------------\n')
#  fp.write('%s\n' % os.getcwd())
#  fp.write('Celery-task wrote it\n')
#  fp.close()
#  d = pyfits.open(queryrows[0].PATH)[0].data
#  astImages.saveBitmap(os.path.join(MEDIA_ROOT,'celery.png'),d,cutLevels=["smart", 99.5],size=300,colorMapName='gray')
#  images =  os.path.join(MEDIA_ROOT,'celery.png') 
  return images
