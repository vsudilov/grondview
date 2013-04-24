from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
import json

from grondview.exceptions import *
from grondview.settings import WORKDIR
from grondview.settings import MEDIA_ROOT
from grondview import tasks

from imagequery.views import ImageHeader

import os,sys
import ConfigParser
import logging


#http://www.pioverpi.net/2012/05/14/ajax-json-responses-using-django-class-based-views/
class JSONResponseMixin(object):  
    def render_to_response(self, context):  
        "Returns a JSON response containing 'context' as payload"  
        return self.get_json_response(self.convert_context_to_json(context))  
  
    def get_json_response(self, content, **httpresponse_kwargs):  
        "Construct an `HttpResponse` object."
        r = HttpResponse(mimetype='application/json',**httpresponse_kwargs)
        r.write(content)
        print r  
        return r
  
    def convert_context_to_json(self, context):  
        "Convert the context dictionary into a JSON object"  
        # Note: This is *EXTREMELY* naive; in reality, you'll need  
        # to do much more complex handling to ensure that arbitrary  
        # objects -- such as Django model instances or querysets  
        # -- can be serialized as JSON.  
        return json.dumps(context)  

class ForceDetectView(JSONResponseMixin,TemplateView):
  def post(self, request, *args, **kwargs):
    try:
      ra = float(request.POST['ra'])
      dec = float(request.POST['dec'])
      targetID = request.POST['TARGETID']
      OB = request.POST['OB']
    except:
      return HttpResponseBadRequest()
    asyncResult = tasks.gr_astrphot.delay('path','iniFile','logger')
    context = {'jobid':asyncResult.id}
    return self.render_to_response(context)
  
  def head(self, request, *args, **kwargs):
    pass

  def get(self, request, *args, **kwargs):
    pass
