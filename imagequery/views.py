from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseBadRequest
import json
from celery.result import AsyncResult

from grondview.settings import PROJECT_ROOT
from grondview.exceptions import *

from forcedetect.views import JSONResponseMixin

from imagequery.models import ImageHeader

import os, sys
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants


def get_fields(formdata,request):
  ra = formdata['ra']
  dec = formdata['dec']
  radius = formdata['radius']
  units = formdata['units']
  results = ImageHeader.objects.positionFilter(ra,dec,radius=radius,units=units)
  if not results:
    raise NoCoverageError(radius=radius,units='arcminutes')
  fields = []
  for i in results:
    fields.append( {'targetID':i.TARGETID,
                    'OB': i.OB,
                    'date_obs': i.DATE_OBS.replace('T',' '),
                    'distance': i.distance*60.0,                    
                    } )

  grouped_fields = []
  for i in fields:
    testcase = [ (j['targetID'],j['OB']) for j in grouped_fields]
    if (i['targetID'],i['OB']) not in testcase:
      grouped_fields.append(i)

  grouped_fields = sorted(grouped_fields, key=lambda k: k['distance'])
  return {'fields':grouped_fields} 



class GetCutouts(JSONResponseMixin,TemplateView):
  def get(self, request, *args, **kwargs):
    pass
  def head(self, request, *args, **kwargs):
    pass
  def post(self, request, *args, **kwargs):
    try:
      targetID, OB = request.POST['currentOB'].split()
      band = request.POST['band']
    except:
      return HttpResponseBadRequest()
  
    jobid = 'abc123'
    context = {'jobid':jobid}
    return self.render_to_response(context)
    
    
    
    
    
    
    
    
    
    
    
    
    
