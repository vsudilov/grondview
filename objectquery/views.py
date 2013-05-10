from django.shortcuts import render
from django.db.models import Q
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView


from grondview.settings import PROJECT_ROOT
from grondview import tasks

from objectquery.forms import ObjectQueryForm
from objectquery.models import AstroSource
from objectquery.models import Photometry
from imagequery.models import ImageHeader

import os, sys
import operator
import json

from astLib import astCoords

sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))
from lib import constants

def get_sources(formdata,request):
  ra = formdata['ra']
  dec = formdata['dec']
  radius = formdata['radius']
  units = formdata['units']
  Qs = [Q(user=request.user), Q(user__username='pipeline')] 
  q = reduce(operator.or_, Qs)
  results = AstroSource.objects.filter(q).positionFilter(ra,dec,radius=radius)   

  if not results:
    #raise NoCoverageError(radius=radius)
    return {'sources':'NO_SOURCES_DETECTED'}

  distances = dict((i.sourceID,i.distance*3600) for i in results) #Keep distance for later
  ownership = dict((i.sourceID,i.user.username) for i in results)  

  #Filter based on sourceID (chaining Q functions)
#  if results:  
#    Qs = [Q(astrosource__sourceID=i.sourceID) for i in results]
#    q = reduce(operator.or_, Qs)
#    results = list(Photometry.objects.filter(q))
    

  #group results by sourceID

  sources = []
  for r in results:
    sources.append( {'name':r.sourceID,'distance':distances[r.sourceID],'ownership':ownership[r.sourceID]} )
  sources = sorted(sources,key=lambda k: k['distance'])
  return {'sources':sources}



class ObjectView(TemplateView):
  template_name = 'content.html'
  sourceID = None #Passed from urls.py|kwargs

  def get(self,request,*args,**kwargs):
    sourceID = self.kwargs['sourceID']
    try:
      thisSource = AstroSource.objects.get(sourceID=sourceID)
    except AstroSource.DoesNotExist:
      return Http404    
    if thisSource.user != request.user and thisSource.user.username != "pipeline":
      #We should make this more robust, ie this will fail if two users "own" the same sourceID
      #Perhaps change the userfield to a M2M field and test if user is in the list?
      raise PermissionDenied
    results = Photometry.objects.filter(astrosource__sourceID=sourceID)
    if not results:
      raise Http404
    #1. Create unique master keys, assuming uniqueness of the concat of TARGETID+OB
    unique_observations = set(["%s %s" % (i.imageheader.TARGETID,i.imageheader.OB) for i in results])
    data = dict([(_id,{}) for _id in unique_observations])

    #2. Populate fields
    for _id in unique_observations:        
      data[_id]['images'] = dict( [(b,None) for b in constants.grondfilters] )
      data[_id]['photometry'] = dict( [(b,{}) for b in constants.grondfilters] )

      #2a.  Populate the properties that are OB (not band) specific
      targetID, OB = _id.split()
      p = results.filter(imageheader__OB=OB).filter(imageheader__TARGETID=targetID)[0].imageheader.PATH
      p = os.path.dirname(os.path.dirname(p)) #Get from ...target/r/GROND_ana.fits to ../target
      thisOB = results.filter(imageheader__PATH__startswith=p)
      data[_id]['OBname'] = thisOB[0].imageheader.OB
      data[_id]['OBtype'] = thisOB[0].imageheader.OBTYPEID
      data[_id]['targetID'] = thisOB[0].imageheader.TARGETID
      data[_id]['MJD'] = thisOB[0].imageheader.MJD_OBS
      for band_specific_data in thisOB:
        #2b.  Populate the photometry fields:
        ht_photometry = {
          'MAG_PSF':      lambda p: round(p.MAG_PSF,2) if p.MAG_PSF else None,
          'MAG_PSF_ERR':  lambda p: round(p.MAG_PSF_ERR,2) if p.MAG_PSF_ERR else None,
          'MAG_APP':      lambda p: round(p.MAG_APP,2) if p.MAG_APP else None,
          'MAG_APP_ERR':  lambda p: round(p.MAG_APP_ERR,2) if p.MAG_APP_ERR else None,
          'ownership':    lambda p: p.user.username,
        }
        data[_id]['photometry'][band_specific_data.BAND] = {}
        for k in ht_photometry:        
          data[_id]['photometry'][band_specific_data.BAND][k] = ht_photometry[k](band_specific_data)

        if band_specific_data.BAND in constants.optical:
          #These will be potentially overwritten by every band in constants.optical
          #This shouldn't be a problem, since the CALIB_SCHEME+FILE should
          #be the same among all optical bands within a particular observation
          data[_id]['griz_calib_scheme'] = band_specific_data.CALIB_SCHEME
          #Consider if we really want/need to expose system pathnames to the client
          data[_id]['griz_calib_file'] = band_specific_data.CALIB_FILE
    #  Find the nominal OB with which to make the initial image cutouts and SED. The nominal OB will 
    #  be image with the most detections, followed by the longest exposure time.
    data_statistics = {}
    for observation in data:
      data_statistics[observation] = {}
      data_statistics[observation]['NIMGS'] = len(data[observation]['images'])
      try:
        data_statistics[observation]['DEPTH'] = constants.obtypes_sequence[data[observation]['OBtype']] #Smaller value = deeper
      except KeyError:
        data_statistics[observation]['DEPTH'] = 100
    t = sorted([ (k,v) for k,v in data_statistics.iteritems()], key = lambda k: k[1]['NIMGS'], reverse=True)  #Sort by the numbers of images
    t = [i for i in t if i[1]['NIMGS'] == t[0][1]['NIMGS']]  #Remove all observations whose NIMGS are less than the max found
    t = sorted(t,key = lambda k: k[1]['DEPTH'])[0] #Take the deepest observation (random choice if multiple OBs at same depth)
    nominalOB = t[0] #Finally, return the TARGETID+OB key that cooresponds to the choosen observation
    

    imageheaders = ImageHeader.objects.getBestImages(
      results[0].astrosource.RA,
      results[0].astrosource.DEC,
      forceOB=nominalOB.split()[1],
      )
    #data[nominalOB]['images']
    for i in imageheaders:
      data[nominalOB]['images'][i.FILTER] = i.fname
    context = {'source_data':json.dumps(data),'request':request,'nominalOB':nominalOB,'astrosource':thisSource}
    return render(request,self.template_name,context)

  def post(self,request,*args,**kwargs):
    pass
  
