from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.utils.importlib import import_module
from django.views.generic import TemplateView

from .forms import LoginForm
from .settings import PROJECT_ROOT
from .settings import MEDIA_ROOT
from . import tasks
from .exceptions import *

from imagequery.models import ImageHeader

from imagequery.forms import ImageQueryForm
from objectquery.forms import ObjectQueryForm

from objectquery.views import get_sources
from imagequery.views import get_fields

from astLib import astCoords

import sys,os
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants




class Authentication(TemplateView):
  template_name = 'login.html'
  form_class = LoginForm
  method = None #Set in urls.py

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      username = request.POST['username']
      passwd = request.POST['passwd']
      user = auth.authenticate(username=username, password=passwd)
      if user is not None:
        if user.is_active:
          auth.login(request, user)
          # Redirect to a success page.
        return HttpResponseRedirect('/')
    return render(request,'login.html',{'form': form, 'invalid_login':True})
  def get(self, request, *args, **kwargs):
      return render(request,'login.html',{'form': self.form_class})

  def dispatch(self, request, *args, **kwargs):
    if self.method == 'logout':
      auth.logout(request)
      return HttpResponseRedirect('/')
    return super(Authentication, self).dispatch(request, *args, **kwargs)        


class FormView(TemplateView):  
  template_name= 'content.html'
  form_class = None #Set in urls.py
  translation = {
    'ObjectQueryForm':get_sources,
    'ImageQueryForm':get_fields,
  } 
  def get(self,request):
    form = self.form_class
    return render(request, self.template_name, {'form':form})

  def post(self,request):
    form = self.form_class(request.POST)

    if not form.is_valid():
      return render(request,self.template_name,{'form': form})    
    try:
      cd = form.cleaned_data
      formdata=self.parseForm(cd)
      ra = formdata['ra']
      dec = formdata['dec']
      radius = formdata['radius']
      units = formdata['units']
      imageheaders = ImageHeader.objects.getBestImages(ra,dec,clipSize=radius,seeing_limit=2.0,units=units)
      context=self.translation[form.__class__.__name__](formdata,request)
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST})      
    context.update( {'form':form,'imageheaders':imageheaders,'request':request.POST} )
    return render(request,'content.html',context)

  def parseForm(self,cd):
    coordstr = cd['coords'].replace(',',' ').strip()
    try:  
      radius = cd['radius_arcmin']
      units = 'arcminutes'
    except KeyError:
      radius = cd['radius_arcsec']
      units = 'arcseconds'
    try:
      include_user_detections = cd['include_user_detections']
    except KeyError:
      include_user_detections = None

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
      radius = min(float(radius),300)
    except:
      raise AreaParseError

    formdata = {
      'radius':radius,
      'ra':ra,
      'dec':dec,
      'units':units,
      'include_user_detections': include_user_detections
      }
    return formdata



class StaticView(TemplateView):
  template_name= 'home.html'

  def get(self,request, *args, **kwargs):
    if 'page_name' in self.kwargs:
      self.template_name = self.kwargs['page_name']
    return render(request, self.template_name)

