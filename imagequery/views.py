from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

from grondview.settings import ROOT_PROJECT
from grondview.settings import MEDIA_ROOT
from imagequery.forms import ImageQueryForm
from imagequery.models import image_header

import os, sys
import numpy as np

import astLib
from astLib import astCoords

class CoordinateParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse coordinates"

class AreaParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse area"

class NoCoverage(Exception):
  def __init__(self):
    self.msg = "No GROND data in that area"

def make_images(cd):
  bands = cd['bands']
  radius = cd['radius']
  coordstr = cd['coords'].replace(',',' ').strip()

  #Validate user input
  #Should implement at least basic client-side js validation later
  if ':' in coordstr:
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
    float(radius)
  except:
    raise AreaParseError
  # -- 

  for img in image_header.objects.order_by('TARGETID'):
    pass
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
    except (AreaParseError,CoordinateParseError,NoCoverage) as e:
      return render(request,'imagequery.html',{'form': form,'formerror':e.msg,'request':request.POST})    
  else:
    return render(request, 'imagequery.html',{'form':ImageQueryForm})
