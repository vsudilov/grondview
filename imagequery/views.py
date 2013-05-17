from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import Http404
from celery.result import AsyncResult

from grondview.settings import PROJECT_ROOT
from grondview.exceptions import NoCoverageError
from grondview import tasks

from objectquery.models import Photometry

from forcedetect.views import JSONResponseMixin

from imagequery.models import ImageHeader

import os, sys
import json
import uuid
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants


def get_fields(formdata,request,imageheaders):
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


class FieldView(TemplateView):
  template_name = 'content.html'
  def get(self, request, *args, **kwargs):
    if 'OB' in kwargs:
      results = ImageHeader.objects.filter(TARGETID=kwargs['targetID'],OB=kwargs['OB'])
      if not results:
        return Http404
      results = sorted(results, key = lambda k: constants.band_sequence[k.FILTER])
      photo_objs = []
      for i in results:
        if i.FILTER in constants.optical:
          photo_objs.extend(Photometry.objects.filter(imageheader=i,BAND=i.FILTER))
      calib_schemes = [j.CALIB_SCHEME for j in photo_objs]
      griz_calib_scheme = calib_schemes[0] if len(set(calib_schemes)) == 1 else 'mixed'
      hashtable = {
        'SEEING': lambda i: round(i.imageproperties.SEEING,2),
        'LIMITING_MAG_3S_ZP': lambda i: round(i.imageproperties.LIMITING_MAG_3S_ZP,1),
        'LIMITING_MAG_3S_CALIB': lambda i: round(i.imageproperties.LIMITING_MAG_3S_CALIB,1),
        'ASTROMETRY_ACCURACY_RA': lambda i: round(i.imageproperties.ASTROMETRY_ACCURACY_RA,2),
        'ASTROMETRY_ACCURACY_DEC': lambda i: round(i.imageproperties.ASTROMETRY_ACCURACY_DEC,2),
        'APP_SIZE': lambda i: round(i.imageproperties.APP_SIZE,1),
        'MEAN_AIRMASS': lambda i: round(i.imageproperties.MEAN_AIRMASS,2),
        'date': lambda i: i.DATE_OBS.split('T')[0],
        'time': lambda i: i.DATE_OBS.split('T')[1][:-4],
        'OBTYPEID': lambda i: i.OBTYPEID,
        'fname': lambda i: tasks.makeImage(i,'%s.png' % uuid.uuid4(),None,None,None).fname,
      }
      data = {}
      for ih in results:
        data[ih.FILTER] = dict([(k,hashtable[k](ih)) for k in hashtable])
        data[ih.FILTER].update({'griz_calib_scheme':griz_calib_scheme})
      context = {'ob_data':json.dumps(data),'targetID':kwargs['targetID'],'OB':kwargs['OB']}
    else:
      results = ImageHeader.objects.filter(TARGETID=kwargs['targetID'])
      if not results:
        return Http404
      hashtable = {
        'date':lambda i: i.DATE_OBS.split('T')[0],
        'time': lambda i: i.DATE_OBS.split('T')[1][:-4],
        'obtype': lambda i: i.OBTYPEID,
        'n_bands': lambda i: len(ImageHeader.objects.filter(TARGETID=i.TARGETID,OB=i.OB)),
        'mjd': lambda i: i.MJD_OBS,
        'filename': lambda i: i.PATH,
      }

      #unique_observations = set([(i.TARGETID,i.OB) for i in results])
      data = {}
      for ih in results:
        if "%s %s" % (ih.TARGETID,ih.OB) not in data:
          data["%s %s" % (ih.TARGETID,ih.OB)] = dict([(k,hashtable[k](ih)) for k in hashtable])
      context = {'field_data':json.dumps(data),'targetID':kwargs['targetID']}
    return render(request,self.template_name,context)

class GetCutouts(JSONResponseMixin,TemplateView):
  def get(self, request, *args, **kwargs):
    try:
      jobid = request.GET['jobid']
    except:
      return HttpResponseBadRequest()
    job = AsyncResult(jobid)
    completed = job.ready()
    if not completed:
      context = {'completed':False}
    else:
      result = job.get()
      context = {'completed':True,'fname':result.fname,'band':result.FILTER}
      
    return self.render_to_response(context)

  def head(self, request, *args, **kwargs):
    pass
  def post(self, request, *args, **kwargs):
    try:
      targetID, OB = request.POST['currentOB'].split()
      band = request.POST['band']
      ra = float(request.POST['ra'])
      dec = float(request.POST['dec'])
    except:
      return HttpResponseBadRequest()
    ih = ImageHeader.objects.filter(TARGETID=targetID).filter(OB=OB).filter(FILTER=band)
    if not ih:
      context = {'jobid':None,'fname':None}
    else:
      ih = ih[0]
      fname = '%s.png' % uuid.uuid4()
      ih.fname = fname
      job = tasks.makeImage.delay(ih,fname,10,ra,dec) 
      context = {'jobid':job.id,'fname':fname}
    return self.render_to_response(context)
    
    
    
    
    
    
    
    
    
    
    
    
    
