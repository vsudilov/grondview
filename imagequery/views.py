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

import astropy
#coordinates subpackage not available in 0.1 ouch
#from astropy import coordinates as coord
#from astropy import units


def make_images(cd):
 #Will use astropy coords to calc arclen
#  def arclen(ra1,ra2,dec1,dec2):
#    def cosd(degs):
#      return np.cos(degs*np.pi/180)
#    return (    (    (ra1-ra2)*cosd(  (dec1+dec2)/2.0  )  )**2 + (dec1-dec2)**2)**(1/2.)*60.*60.

  bands = cd['bands']
  coordstring = cd['coords']
  area = cd['area']
  user_coord = coord.ICRSCoordinates(str(coordstring), unit=(None, None))
  #Remember possibilty of mixed up ra,dec
  db_coord = coord.ICRSCoordinates(ra=ra, dec=dec, unit=(units.degree, units.degree))
  sep = db_coord.separation(user_coord)    
  if sep.arcmins <= area:
    rows.append(result)
  return images

def home(request):
  if request.method == 'POST':
    form = ImageQueryForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      images=make_images(cd)
      return render(request,'imagequery.html',{'form': ImageQueryForm,'images':images,'request':request.POST})
  return render(request, 'imagequery.html',{'form':ImageQueryForm})
