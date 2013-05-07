from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
import json
from celery.result import AsyncResult

from grondview.exceptions import *
from grondview.settings import GP_INIDIR
from grondview.settings import MEDIA_ROOT
from grondview.settings import PROJECT_ROOT
from grondview import tasks

from objectquery.models import Photometry
from objectquery.models import AstroSource

from forcedetect.models import UserTask_photometry

import os,sys
import ConfigParser
import logging

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants

#http://www.pioverpi.net/2012/05/14/ajax-json-responses-using-django-class-based-views/
class JSONResponseMixin(object):  
    def render_to_response(self, context):  
        "Returns a JSON response containing 'context' as payload"  
        return self.get_json_response(self.convert_context_to_json(context))  
  
    def get_json_response(self, content, **httpresponse_kwargs):  
        "Construct an `HttpResponse` object."
        return HttpResponse(content,mimetype='application/json',**httpresponse_kwargs)
  
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
      targetID = request.POST['targetID']
      OB = request.POST['OB']
      band = request.POST['band']
      sourceID = request.POST['sourceID']
    except:
      return HttpResponseBadRequest()

    current_user_tasks = UserTask_photometry.objects.filter(user=request.user)
    if len(current_user_tasks) > 3:
      return HttpResponseBadRequest("Too many requests from user [%s]" % request.user.username)

    #Find path, iniFile, logger; create task
    iniFile = os.path.join(GP_INIDIR,targetID,OB,'%sana.ini' % band)
    objwcs = (ra,dec)
    task = tasks.photometry.delay(iniFile, objwcs)
    context = {'jobid':task.id}

    #Make a database entry for the current task.
    fields = {}
    fields['user'] = request.user
    fields['jobid'] = task.id
    fields['band'] = band
    fields['sourceID'] = sourceID
    fields['OB'] = OB
    fields['logfile_line_number'] = 0
    db_entry = UserTask_photometry(**fields)
    db_entry.save()
    return self.render_to_response(context)
  
  def head(self, request, *args, **kwargs):
    pass

  def get(self, request, *args, **kwargs):
    jobid = self.kwargs['jobid']
    job = AsyncResult(jobid)
    completed = job.ready()
    db_entry = UserTask_photometry.objects.get(jobid=jobid)
    lastline = db_entry.logfile_line_number
    with open(os.path.join(MEDIA_ROOT,jobid,'logfile'),'r') as f:
      lines = f.readlines()
    if not completed or lastline < len(lines):
        loglines = ''.join(lines[lastline:]).strip()
        loglines = loglines.replace('\n','<br />')
        db_entry.logfile_line_number = len(lines)
        db_entry.save()
        context = {'completed':False,'log':loglines}
    else:
      results = job.get()
      mag = round(results['APP'][2],2)
      mag_err = round(results['APP'][3],2)
      context = {'completed':True,'jobid':jobid,'mag':mag,'mag_err':mag_err}

      hashtable = {
            'MAG_APP': lambda d: d['APP'][2] if d['APP'] else None,
            'MAG_APP_ERR': lambda d: d['APP'][3] if d['APP'] else None,
            'MAG_PSF': lambda d: d['PSF'][2] if d['PSF'] else None,
            'MAG_PSF_ERR': lambda d: d['PSF'][3] if d['PSF'] else None,
      }
      fields = {}
      fields['user'] = request.user
      fields['BAND'] = db_entry.band
      o = Photometry.objects.filter(astrosource__sourceID=db_entry.sourceID)[0]
      fields['imageheader'] = o.imageheader
      fields['astrosource'] = o.astrosource
      [fields.update( {k:hashtable[k](results)} ) for k in hashtable.keys()]
      p = Photometry(**fields)
      p.save()
      db_entry.delete() #Delete database entry, this should eventually be tied to the redis backend!
    return self.render_to_response(context)



















