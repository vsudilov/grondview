from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404

from grondview.settings import PROJECT_ROOT
from grondview.settings import MEDIA_ROOT
from grondview import tasks
from grondview.views import GenericDataContainer
from objectquery.forms import ObjectQueryForm
from objectquery.models import AstroSource
from objectquery.models import Photometry
from imagequery.models import ImageHeader

import os, sys
import operator
import uuid
import numpy as np

from astLib import astCoords

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants



#------------------------------------------
# Custom exceptions
class CoordinateParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse coordinates"

class AreaParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse area"
class NoCoverageError(Exception):
  def __init__(self,radius):
    self.msg = "No GROND objects within %0.1f arcsecond(s) of given coordinates" % radius
#------------------------------------------


def get_sources(cd):
  coordstr = cd['coords'].replace(',',' ').strip()
  radius = cd['radius']

  #-------------------------------------
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
  #-------------------------------------
  results = AstroSource.objects.sourcePositionFilter(ra,dec,radius=radius,units='arcseconds')
    
  if not results:
    raise NoCoverageError(radius=radius)
  distances = dict((i.sourceID,i.distance*3600) for i in results) #Keep distance for later

  #Filter based on sourceID (chaining Q functions)
  Qs = [Q(astrosource__sourceID=i.sourceID) for i in results]
  q = reduce(operator.or_, Qs)
  results = Photometry.objects.filter(q)
  
  #group results by sourceID
  grouped_sources = dict((i.astrosource.sourceID,[]) for i in results)
  for r in results:
    grouped_sources[r.astrosource.sourceID].append(r)
  sources = []

  #Append GenericDataContainers to sources list
  for sourceID in grouped_sources:
    sources.append(GenericDataContainer(name=sourceID,distance=distances[sourceID]))
    for source_data in grouped_sources[sourceID]:
      OBname = source_data.imageheader.OB
      D = source_data.__dict__
      D['imageheader'] = source_data.imageheader #obj.__dict__ gives the ForeignKeys funny names
      D['astrosource'] = source_data.astrosource
      sources[-1].appendOB(OBname=OBname,data=D)
    sources[-1].sortOBs()
    sources[-1].sortBands()
  sources = sorted(sources,key=lambda k: k.distance)
  
  #Find imageheaders that will be plotted. Plot the "best", which has the following criteria:
  #1. 7 filters (exact)
  #2. depth (30m,20m,10m,8m,4m)
  #3. seeing
  SEEING_LIMIT = 2.0
  candidateOBs = {}
  results = ImageHeader.objects.filter(imageproperties__SEEING__lte=SEEING_LIMIT).imagePositionFilter(ra,dec,radius)
  for r in results:
    try:
      candidateOBs[r.TARGETID+r.OB].append(r)
    except KeyError:
      candidateOBs[r.TARGETID+r.OB] = [r]

  max_filters = len(max(sorted(candidateOBs.values(), key=len)))
  candidateOBs = [i for i in candidateOBs.values() if len(i)==max_filters]
  imageheaders = sorted(candidateOBs, key = lambda k: constants.obtypes_sequence[k[0].OBTYPEID])[0]
  #Create image cut-outs
  clipSizeArcsec = radius
  clipSizeArcsec *= 10 #for binned stubdata!
  for hdr in imageheaders:
    fname = '%s.png' % uuid.uuid4()
    hdr.fname = fname #This attribute is expected by the template
    tasks.makeImage(hdr,fname,clipSizeArcsec,ra,dec)

  return sources,imageheaders


def view_source(request,sourceID):
  results = Photometry.objects.filter(astrosource__sourceID=sourceID)
  if not results:
    raise Http404

  '''
  Find the nominal OB with which to make image cutouts and SED. The nominal OB will 
  be image with the most detections, followed by the longest exposure time. Additionally,
  there is a seeing limit imposed on all OBs
  '''
  OBs = [i.imageheader.OB for i in results]
  TARGETIDs = [i.imageheader.TARGETID for i in results] #Necessary if there happen to be multiple IDs per field
  SEEING_LIMIT = 2.0
  candidateOBs = {}
  for TARGETID in TARGETIDs:
    for OB in OBs:
      photo_objs = (Photometry.objects
                  .filter(astrosource__sourceID=sourceID)
                  .filter(imageheader__imageproperties__SEEING__lte=SEEING_LIMIT)
                  .filter(imageheader__OB=OB)
                  .filter(imageheader__TARGETID=TARGETID)
                  )
      if not photo_objs:
        continue
      candidateOBs[TARGETID+OB] = photo_objs

  max_filters = len(max(sorted(candidateOBs.values(), key=len)))
  candidateOBs = [i for i in candidateOBs.values() if len(i)==max_filters]  
  for i in candidateOBs:
    print i
  nominalOB = sorted(candidateOBs, key = lambda k: constants.obtypes_sequence[k[0].imageheader.OBTYPEID])[0]
  nominalOB = sorted(nominalOB, key=lambda k: constants.band_sequence[k.BAND])
  
  #Create image cut-outs
  clipSizeArcsec= 10 #10 arcseconds
  clipSizeArcsec *= 10 #for binned stubdata!
  imageheaders = ImageHeader.objects.filter(OB=nominalOB[0].imageheader.OB).filter(TARGETID=nominalOB[0].imageheader.TARGETID)
  imageheaders = sorted(imageheaders, key=lambda k: constants.band_sequence[k.FILTER])
  ra = nominalOB[0].astrosource.RA
  dec = nominalOB[0].astrosource.DEC
  for hdr in imageheaders:
    fname = '%s.png' % uuid.uuid4()
    hdr.fname = fname #This attribute is expected by the template
    tasks.makeImage(hdr,fname,clipSizeArcsec,ra,dec)

  #For SEDs
  x,y,yerr = [],[],[]
  for photo_obj in nominalOB:
    x.append(constants.GrondFilters[photo_obj.BAND]['lambda_eff'])
    if photo_obj.BAND in 'griz':
      mag = photo_obj.MAG_PSF
      mag_err = photo_obj.MAG_PSF_ERR
    else:
      mag = photo_obj.MAG_CALIB
      mag_err = photo_obj.MAG_CALIB_ERR
    y.append(mag)
    yerr.append( [mag-mag_err,mag+mag_err] )
  SED = dict(x=x,y=y,yerr=yerr)

  #Set up the data container that will be iterated/presented in the html template
  userColumns = (
          'OBtype',
          'OBname',
          'g','g_err',
          'r','r_err',
          'i','i_err',
          'z','z_err',
          'J','J_err',
          'H','H_err', 
          'K','K_err') #This should eventually be a user input
          
  magnitude_kws = (
          'g','g_err',
          'r','r_err',
          'i','i_err',
          'z','z_err',
          'J','J_err',
          'H','H_err', 
          'K','K_err',
          )

  translation = {
                'OBtype': lambda k: k.imageheader.OBTYPEID,
                'OBname': lambda k: k.imageheader.OB,
                'g': lambda k: k.MAG_PSF,
                'r': lambda k: k.MAG_PSF,
                'i': lambda k: k.MAG_PSF,
                'z': lambda k: k.MAG_PSF,
                'J': lambda k: k.MAG_CALIB+constants.convert_to_AB['J'],
                'H': lambda k: k.MAG_CALIB+constants.convert_to_AB['H'],
                'K': lambda k: k.MAG_CALIB+constants.convert_to_AB['K'],

                'g_err': lambda k: k.MAG_PSF_ERR,
                'r_err': lambda k: k.MAG_PSF_ERR,
                'i_err': lambda k: k.MAG_PSF_ERR,
                'z_err': lambda k: k.MAG_PSF_ERR,
                'J_err': lambda k: k.MAG_CALIB_ERR,
                'H_err': lambda k: k.MAG_CALIB_ERR,
                'K_err': lambda k: k.MAG_CALIB_ERR,
                }
  source_data = []
  for OB in set(OBs):
    source_data.append( dict([(k,'') for k in userColumns]) )
    for r in results.filter(imageheader__OB=OB):
      D = {}
      D['imageheader'] = r.imageheader
      for column in userColumns:
        if column not in magnitude_kws:
          D[column] = translation[column](r)
      if r.BAND in userColumns:
        D[r.BAND] = '%0.2f' % translation[r.BAND](r)
        D[r.BAND+"_err"] = '%0.2f' % translation[r.BAND+"_err"](r)
      source_data[-1].update(D)
  
  lightcurve = {}
  for band in constants.bands:
    x,y,yerr = [],[],[] #For lightcurve
    #TODO: Allow user to choose which band is plotted in the LC
    for OB in source_data:
      if OB[band]:
        mag = round(float(OB[band]),2) #Convert back to float from formatted string
        mag_err = round(float(OB[band+"_err"]),2)
        x.append(round(OB['imageheader'].MJD_MID,2))
        y.append(mag)
        yerr.append([ mag-mag_err,mag+mag_err ])
    lightcurve[band] = {'x':x,'y':y,'yerr':yerr}
  bestBand = sorted(lightcurve.items(),key=lambda k: len(k[1]['x']), reverse=True)[0][0]
  return render(request,'content.html',{'source_data':source_data,'request':request,
                                        'lightcurve':lightcurve[bestBand],'nominalOB':nominalOB,
                                        'SED':SED,'userColumns':userColumns,'lc_band':bestBand,
                                        'imageheaders':imageheaders,
                                        })


def home(request):
  if request.method == 'POST':
    form = ObjectQueryForm(request.POST)
    if not form.is_valid():
      return render(request,'content.html',{'form': form})
    cd = form.cleaned_data
    try:
      sources,imageheaders=get_sources(cd)
      return render(request,'content.html',{'form': form,'sources':sources,'imageheaders':imageheaders,'request':request.POST})
    except (AreaParseError,CoordinateParseError,NoCoverageError) as e:
      return render(request,'content.html',{'form': form,'formerror':e.msg,'request':request.POST})    
  else:
    return render(request, 'content.html',{'form':ObjectQueryForm})
