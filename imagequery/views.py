from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

from grondview.settings import PROJECT_ROOT
from grondview.settings import MEDIA_ROOT
from grondview import tasks
from imagequery.forms import ImageQueryForm
from imagequery.models import ImageHeader

import os, sys
import uuid
import numpy as np

from astLib import astCoords

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants


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


def get_images(cd,radius=10):
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
    area = float(area)
    area *= constants.convert_arcmin_or_arcsec_to_degrees[unit_area]
  except:
    raise AreaParseError
  #-------------------------------------
  
  results = ImageHeader.objects.filter(FILTER__in=bands).imagePositionFilter(ra,dec,radius=radius,units='degrees')
  if not results:
    raise NoCoverageError(radius=radius)
  images = []

  #Initialize the python data structure that will be expanded in the html-template:
  # targets = {TARGETID:{OB:[{band:x,PATH_RAW:x,PATH_PNG:x,DATE_OBS:x},...],...},...}
  targetIDs = [r.TARGETID for r in results]
  targets = dict([(t,{}) for t in targetIDs])  

  for i in results:
    image = {} # -- Sanitize the database results, prepare to give the task to celery
    image['DATE_OBS'] = i.DATE_OBS.replace('T',' ')
    unique_filename = uuid.uuid4()
    fname = '%s.png' % unique_filename
    image['PATH_PNG'] = fname
    image['PATH_RAW'] = i.PATH
    image['BAND'] = i.FILTER
    tasks.makeImage.delay(image,area,ra,dec)
    if not targets[i.TARGETID].has_key(i.OB):
      targets[i.TARGETID][i.OB] = []
    targets[i.TARGETID][i.OB].append(image)
  return targets

def home(request):
  if request.method == 'POST':
    form = ImageQueryForm(request.POST)
    if not form.is_valid():
      return render(request,'content.html',{'form': form})
    cd = form.cleaned_data
    try:
      targets=get_images(cd)
      return render(request,'content.html',{'form': form,'targets':targets,'request':request.POST})
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST})    
  else:
    return render(request, 'content.html',{'form':ImageQueryForm})
