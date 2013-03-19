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
from grondview.views import GenericDataContainer
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
  distances = dict((i.sourceID,i.distance*3600) for i in results) #Keep distance for later

  #Filter based on sourceID (chaining Q functions)
  Qs = [Q(astrosource__sourceID=i.sourceID) for i in results]
  q = reduce(operator.or_, Qs)
  results = Photometry.objects.filter(q)
  
  #group results by sourceID
  grouped_sources = dict((i.astrosource.sourceID,[]) for i in results)
  for r in results:
    grouped_sources[r.astrosource.sourceID].append(r)
  sources = []

  #Append GenericDataContainers to sources list
  for sourceID in grouped_sources:
    sources.append(GenericDataContainer(name=sourceID,distance=distances[sourceID]))
    for source_data in grouped_sources[sourceID]:
      OBname = source_data.imageheader.OB
      D = source_data.__dict__
      D['imageheader'] = source_data.imageheader #obj.__dict__ gives the ForeignKeys funny names
      D['astrosource'] = source_data.astrosource
      sources[-1].appendOB(OBname=OBname,data=D)
    sources[-1].sortOBs()
    sources[-1].sortBands()
  sources = sorted(sources,key=lambda k: k.distance)
  return sources


def view_source(request,sourceID):
  results = get_list_or_404(Photometry.objects.filter(astrosource__sourceID=sourceID))
  source = GenericDataContainer(name=sourceID)
  for r in results:
    OB = r.imageheader.OB
    D = {}
    D = r.__dict__
    D['imageheader'] = r.imageheader #obj.__dict__ gives the ForeignKeys funny names
    D['astrosource'] = r.astrosource
    source.appendOB(OBname=OB,data=D,OBtype=r.imageheader.OBTYPEID)

  source.sortOBs()
  source.sortBands()
  
  for OB in source.OBs: #For SEDs
    x,y,yerr = [],[],[]
    for d in OB.data:
      x.append(constants.GrondFilters[d['BAND']]['lambda_eff'])
      y.append(d['MAG_PSF'])
      yerr.append(d['MAG_PSF_ERR'])
    OB.SED = [dict([('x',i),('y',j),('err',k)]) for i,j,k in zip(x,y,yerr)]


  x,y,yerr = [],[],[] #For lightcurve
  for OB in source.OBs:
    x.append(OB.data[0]['imageheader'].MJD_MID)
    y.append(OB.data[0]['MAG_PSF'])
    yerr.append(OB.data[0]['MAG_PSF_ERR'])
    
  lightcurve = [dict([('x',i),('y',j),('err',k)]) for i,j,k in zip(x,y,yerr)]
  return render(request,'content.html',{'source':source,'request':request,'lightcurve':lightcurve})


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
