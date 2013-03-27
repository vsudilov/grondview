from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from grondview.settings import PROJECT_ROOT
from grondview.settings import MEDIA_ROOT
from grondview import tasks
from grondview.views import GenericDataContainer
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
  distances = dict((i.TARGETID,i.distance*3600) for i in results) #Keep distance for later

  #group results by targetID
  grouped_targets = dict((i.TARGETID,[]) for i in results)
  images = dict([(i.TARGETID,[]) for i in results])  
  for r in results:
    grouped_targets[r.TARGETID].append(r)
  targets = []

  #Append GenericDataCounters to targets list
  for targetID in grouped_targets:
    targets.append(GenericDataContainer(name=targetID,distance=distances[targetID]))
    for source_data in grouped_targets[targetID]:
      OBname = source_data.OB
      date_obs = source_data.DATE_OBS.replace('T',' ')
      D = source_data.__dict__
      D['DATE_OBS'] = date_obs
      D['BAND'] = D['FILTER'] #For sorting to work
      unique_filename = uuid.uuid4()
      fname = '%s.png' % unique_filename
      D['PATH_PNG'] = fname
      D['PATH_RAW'] = source_data.PATH
      tasks.makeImage.delay(D,area,ra,dec)
      targets[-1].appendOB(OBname=OBname,date_obs=date_obs,data=D)
    targets[-1].sortOBs()
    targets[-1].sortBands()
  targets = sorted(targets,key=lambda k: k.distance)
  return targets







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
