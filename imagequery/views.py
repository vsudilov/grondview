from django.shortcuts import render

from grondview.settings import PROJECT_ROOT
from grondview.exceptions import *
from .models import ImageHeader

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
    print testcase
    if (i['targetID'],i['OB']) not in testcase:
      grouped_fields.append(i)

  grouped_fields = sorted(grouped_fields, key=lambda k: k['distance'])
  return {'fields':grouped_fields} 
