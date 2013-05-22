from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.utils.importlib import import_module
from django.views.generic import TemplateView
from django.db.models import Q
from django.db.models import Count

from .forms import LoginForm
from .settings import PROJECT_ROOT
from .settings import MEDIA_ROOT
from . import tasks
from .exceptions import *

from imagequery.models import ImageHeader
from objectquery.models import AstroSource

from imagequery.forms import ImageQueryForm
from objectquery.forms import ObjectQueryForm

from objectquery.views import get_sources
from imagequery.views import get_fields

from astLib import astCoords

import sys,os
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants



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
      context=self.translation[form.__class__.__name__](formdata,request,imageheaders)
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST})      
    context.update( {'form':form,'imageheaders':imageheaders,'request':request.POST} )
    return render(request,self.template_name,context)

  def parseForm(self,cd):
    coordstr = cd['coords'].replace(',',' ').strip()
    try:  
      radius = cd['radius_arcmin']
      units = 'arcminutes'
    except KeyError:
      radius = cd['radius_arcsec']
      units = 'arcseconds'

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
      radius = max(radius,1)
    except:
      raise AreaParseError

    try:
      n_bands = float(cd['n_bands'])
    except:
      n_bands = None

    try:
      forcedetect = cd['forcedetect']
    except:
      forcedetect = None


    formdata = {
      'radius':radius,
      'ra':ra,
      'dec':dec,
      'units':units,
      'n_bands':n_bands,
      'forcedetect':forcedetect,
      }
    return formdata

class HomeView(TemplateView):
  template_name = 'home.html'
  def get(self,request, *args, **kwargs):
    context = {}
    context['aggData'] = {}
    context['aggData']['totalFields'] = ImageHeader.objects.distinct('TARGETID').count()
    t = AstroSource.objects.filter(user__username='pipeline').annotate(nbands=Count('photometry__BAND',distinct=True))
    context['aggData']['totalPipelineObjects'] = len([i for i in t if i.nbands>=2])
    t = AstroSource.objects.filter(~Q(user__username='pipeline')).annotate(nbands=Count('photometry__BAND',distinct=True))
    context['aggData']['totalUserObjects'] = len([i for i in t if i.nbands>=2])
    s = sum([(i.TOPRIGHT_DEC-i.BOTTOMLEFT_DEC)*(i.BOTTOMLEFT_RA-i.TOPRIGHT_RA) for i in ImageHeader.objects.filter(FILTER='r').distinct('TARGETID')])
    context['aggData']['totalArea_r'] = round(s,3)
    s = sum([(i.TOPRIGHT_DEC-i.BOTTOMLEFT_DEC)*(i.BOTTOMLEFT_RA-i.TOPRIGHT_RA) for i in ImageHeader.objects.filter(FILTER='J').distinct('TARGETID')])
    context['aggData']['totalArea_J'] = round(s,3)
    context['aggData']['totalOBs'] = ImageHeader.objects.distinct('TARGETID','OB').count()
    return render(request, self.template_name, context)


class StaticView(TemplateView):
  template_name= 'content.html'
  def get(self,request, *args, **kwargs):
    if 'page_name' in self.kwargs:
      self.template_name = '%s.html' % self.kwargs['page_name']
    return render(request, self.template_name)

