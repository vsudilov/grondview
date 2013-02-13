from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

from grondview.settings import PROJECT_ROOT
from grondview.settings import MEDIA_ROOT
from imagequery.forms import ImageQueryForm
from imagequery.models import ImageHeader

import os, sys
import uuid
import numpy as np

from astLib import astCoords
from astLib import astImages
import pyfits

#------------------------------------------
# Custom exceptions
class CoordinateParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse coordinates"

class AreaParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse area"
class NoCoverageError(Exception):
  def __init__(self,radius):
    self.msg = "No GROND fields within %s degrees of given coordinates" % radius
#------------------------------------------


def make_images(cd,radius=10):
  bands = cd['bands']
  coordstr = cd['coords'].replace(',',' ').strip()
  area = cd['area']
  unit_area = cd['unit_area']
  
  #-------------------------------------
  # User input data validation
  if ':' in coordstr:
    # Remember to add sanity checks!    
    try:
      c = coordstr.split()
      ra = astCoords.hms2decimal(c[0],':')
      dec = astCoords.dms2decimal(c[1],':') 
    except:
      raise CoordinateParseError
  else:
    try:
      c = coordstr.split()
      ra,dec = map(float,c)
    except:
      raise CoordinateParseError
  try:
    float(area)
  except:
    raise AreaParseError
  #-------------------------------------
  
  results = ImageHeader.objects.filter(FILTER__in=bands).imagePositionFilter(ra,dec,radius=radius,units='degrees')
  if not results:
    raise NoCoverageError(radius=radius)
  paths = [i.PATH for i in results]
  images = []
  for path in paths:
    d = pyfits.open(path)[0].data
    unique_filename = uuid.uuid4()
    fname = '%s.png' % unique_filename
    images.append(fname)
    astImages.saveBitmap(os.path.join(MEDIA_ROOT,fname),d,cutLevels=["smart", 99.5],size=300,colorMapName='gray')
  return images

def home(request):
  if request.method == 'POST':
    form = ImageQueryForm(request.POST)
    if not form.is_valid():
      return render(request,'imagequery.html',{'form': form})
    cd = form.cleaned_data
    try:
      images=make_images(cd)
      return render(request,'imagequery.html',{'form': form,'images':images,'request':request.POST})
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'imagequery.html',{'form': form,'formerror':e.msg,'request':request.POST})    
  else:
    return render(request, 'imagequery.html',{'form':ImageQueryForm})
