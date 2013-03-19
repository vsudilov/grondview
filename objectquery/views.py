from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import get_list_or_404
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from grondview.settings import PROJECT_ROOT
from grondview.settings import MEDIA_ROOT
from grondview import tasks
from objectquery.forms import ObjectQueryForm
from objectquery.models import AstroSource
from objectquery.models import Photometry

import os, sys
import operator
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
    self.msg = "No GROND objects within %0.1f arcsecond(s) of given coordinates" % radius
#------------------------------------------


def get_sources(cd):
  coordstr = cd['coords'].replace(',',' ').strip()
  area = cd['area']

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
    radius = float(area)
  except:
    raise AreaParseError
  #-------------------------------------
  results = AstroSource.objects.sourcePositionFilter(ra,dec,radius=radius,units='arcseconds')
    
  if not results:
    raise NoCoverageError(radius=radius)
  #Initialize the python data structure that will be expanded in the html-template:
  # targets = {sourceID:{OB:[{band:x,MAG_PSF:x,MAG_APP:x},...],...},...}
  sourceIDs = [i.sourceID for i in results]
  distances = dict((i.sourceID,i.distance) for i in results)
  sources = dict((sourceID,{}) for sourceID in sourceIDs)

  #Filter based on sourceID (chaining Q functions)
  Qs = [Q(astrosource__sourceID=sourceID) for sourceID in sourceIDs]
  q = reduce(operator.or_, Qs)
  results = Photometry.objects.filter(q)  

  for obj in results:
    if not sources[obj.astrosource.sourceID].has_key(obj.imageheader.OB):
      sources[obj.astrosource.sourceID][obj.imageheader.OB] = []
    D = {}
    D = obj.__dict__
    D['imageheader'] = obj.imageheader #obj.__dict__ gives the ForeignKeys funny names
    D['astrosource'] = obj.astrosource
    D['distance'] = distances[obj.astrosource.sourceID]
    sources[obj.astrosource.sourceID][obj.imageheader.OB].append(D)
  return sources


def view_source(request,sourceID):
  results = get_list_or_404(Photometry.objects.filter(astrosource__sourceID=sourceID).order_by('imageheader__OB'))
  source = {}
  for r in results:
    OB = r.imageheader.OB
    if not source.has_key(OB):
      source[OB] = []
      x,y,yerr = [],[],[] #For SED
    D = {}
    D = r.__dict__
    D['imageheader'] = r.imageheader #obj.__dict__ gives the ForeignKeys funny names
    D['astrosource'] = r.astrosource
    x.append(constants.GrondFilters[D['BAND']]['lambda_eff'])
    y.append(D['MAG_PSF'])
    yerr.append(D['MAG_PSF_ERR'])
    source[OB].append(D)

  x,y,yerr = [],[],[] #For lightcurve
  for OB in source:
    x.append(source[OB][0]['imageheader'].MJD_MID)
    y.append(source[OB][0]['MAG_PSF'])
    yerr.append(source[OB][0]['MAG_PSF_ERR'])
    
  lightcurve = [dict([('x',i),('y',j),('err',k)]) for i,j,k in zip(x,y,yerr)]
  return render(request,'content.html',{'source':source,'request':request,'sourceID':sourceID,'lightcurve':lightcurve})


def home(request):
  if request.method == 'POST':
    form = ObjectQueryForm(request.POST)
    if not form.is_valid():
      return render(request,'content.html',{'form': form})
    cd = form.cleaned_data
    try:
      sources=get_sources(cd)
      return render(request,'content.html',{'form': form,'sources':sources,'request':request.POST})
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST})    
  else:
    return render(request, 'content.html',{'form':ObjectQueryForm})
