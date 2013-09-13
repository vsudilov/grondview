from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.utils.importlib import import_module
from django.views.generic import TemplateView
from django.db.models import Q
from django.views.generic import View
from django.utils import simplejson

from .forms import LoginForm
from .settings import PROJECT_ROOT
from .settings import MEDIA_ROOT
from . import tasks
from .exceptions import *

from imagequery.models import ImageHeader
from objectquery.models import AstroSource

from imagequery.forms import ImageQueryForm
from objectquery.forms import ObjectQueryForm

from objectquery.views import get_sources, getSourceData
from imagequery.views import get_fields

from astLib import astCoords

import sys,os
import operator
import tempfile
import zipfile
import cPickle as pickle
import datetime
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants

class DownloadImages(View):
  def get(self, request, *args, **kwargs):
    basepath = ImageHeader.objects.filter(TARGETID=kwargs['TARGETID'])[0].PATH
    basepath = os.path.join(basepath[:basepath.rfind(kwargs['TARGETID'])],kwargs['TARGETID'])
    if 'OB' in kwargs:
      basepath = os.path.join(basepath,kwargs['OB'])

    # Do this async via tasks.delay()!!!
    filelist = []
    fextensions = ['ana.fits','.tsv','.reg','.result']
    for path,dir,files in os.walk(basepath):
      for f in files:
        if any([f.endswith(fe) for fe in fextensions]):
          filelist.append(os.path.join(path,f))  

    temp = tempfile.TemporaryFile(dir=MEDIA_ROOT)
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)                          
    [archive.write(f,arcname=f[f.rfind(kwargs['TARGETID']):]) for f in filelist]
    archive.close()
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % kwargs['TARGETID'] 
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response
  def post(self, request, *args, **kwargs):
    pass

class ExportView(View):
  def get(self, request, *args, **kwargs):
    Qs = [Q(user=request.user), Q(user__username='pipeline')] 
    q = reduce(operator.or_, Qs)
    thisSource = AstroSource.objects.filter(sourceID=kwargs['sourceID']).filter(q)[0]
    data = getSourceData(thisSource,request.user)
    rows = []
    header = []
    header.append('# sourceID: %s' % thisSource.sourceID)
    header.append('# ra, dec: %s,%s' % (thisSource.RA,thisSource.DEC))
    header.append('# griz phototype: %s' % request.GET['phototype'])
    header.append('# targetid,ob,obtype,mjd,griz_calib,g,g_err,r,r_err,i,i_err,z,z_err,J,J_err,H,H_err,K,K_err')
    rows.append('\n'.join(header))
    photo_key = 'MAG_APP' if request.GET['phototype']=="APP" else 'MAG_PSF'
    photo_errkey = 'MAG_APP_ERR' if request.GET['phototype']=="APP" else 'MAG_PSF_ERR'
    for k in sorted(data.values(),key=lambda l: l['MJD']):
      row = []
      row.append(k['targetID'])
      row.append(k['OBname'])
      row.append(k['OBtype'])
      row.append(k['MJD'])
      row.append(k.get('griz_calib_scheme','N/A'))
      row.append(k['photometry']['g'].get(photo_key,'NaN'))
      row.append(k['photometry']['g'].get(photo_errkey,'NaN'))
      row.append(k['photometry']['r'].get(photo_key,'NaN'))
      row.append(k['photometry']['r'].get(photo_errkey,'NaN'))
      row.append(k['photometry']['i'].get(photo_key,'NaN'))
      row.append(k['photometry']['i'].get(photo_errkey,'NaN'))
      row.append(k['photometry']['z'].get(photo_key,'NaN'))
      row.append(k['photometry']['z'].get(photo_errkey,'NaN'))
      row.append(k['photometry']['J'].get('MAG_APP','NaN'))
      row.append(k['photometry']['J'].get('MAG_APP_ERR','NaN'))
      row.append(k['photometry']['H'].get('MAG_APP','NaN'))
      row.append(k['photometry']['H'].get('MAG_APP_ERR','NaN'))
      row.append(k['photometry']['K'].get('MAG_APP','NaN'))
      row.append(k['photometry']['K'].get('MAG_APP_ERR','NaN'))
      rows.append(','.join([str(i) for i in row]))
    temp = tempfile.TemporaryFile(dir=MEDIA_ROOT)
    temp.write('\n'.join(rows))
    temp.flush()
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=table.csv'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


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
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST,'no_results':True})      
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
    context = pickle.load(open(os.path.join(PROJECT_ROOT,'aggregate.pickle')))
    ellapsed = datetime.datetime.now()-context['time']
    context['time'] = int(round(ellapsed.seconds/60.0)) #minutes
    return render(request, self.template_name, context)


class StaticView(TemplateView):
  template_name= 'content.html'
  def get(self,request, *args, **kwargs):
    if 'page_name' in self.kwargs:
      self.template_name = '%s.html' % self.kwargs['page_name']
    return render(request, self.template_name)

