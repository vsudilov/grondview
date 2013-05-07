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
  sourceID = None #Set in urls.py

  def get(self,request,*args,**kwargs):
    sourceID = self.kwargs['sourceID']
    if 'user' in self.kwargs:
      if AstroSource.objects.get(sourceID=sourceID).user != request.user:
        raise PermissionDenied
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
    ra = results[0].astrosource.RA
    dec = results[0].astrosource.DEC
    
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

    max_filters = max( [len(i) for i in candidateOBs.values()] )
    candidateOBs = [i for i in candidateOBs.values() if len(i)==max_filters]  
    nominalOB = sorted(candidateOBs, key = lambda k: constants.obtypes_sequence[k[0].imageheader.OBTYPEID])[0]
    nominalOB = sorted(nominalOB, key=lambda k: constants.band_sequence[k.BAND])

    #For SEDs
    x,y,yerr = [],[],[]
    for photo_obj in nominalOB:
      x.append(constants.GrondFilters[photo_obj.BAND]['lambda_eff'])
      if photo_obj.BAND in 'griz':
        mag = photo_obj.MAG_PSF if photo_obj.MAG_PSF else photo_obj.MAG_CALIB
        mag_err = photo_obj.MAG_PSF_ERR if photo_obj.MAG_PSF_ERR else photo_obj.MAG_CALIB_ERR
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
                  'targetID': lambda k: k.imageheader.TARGETID,
                  'OBtype': lambda k: k.imageheader.OBTYPEID,
                  'OBname': lambda k: k.imageheader.OB,
                  'g': lambda k: k.MAG_PSF if k.MAG_PSF else k.MAG_CALIB,
                  'r': lambda k: k.MAG_PSF if k.MAG_PSF else k.MAG_CALIB,
                  'i': lambda k: k.MAG_PSF if k.MAG_PSF else k.MAG_CALIB,
                  'z': lambda k: k.MAG_PSF if k.MAG_PSF else k.MAG_CALIB,
                  'J': lambda k: k.MAG_CALIB+constants.convert_to_AB['J'],
                  'H': lambda k: k.MAG_CALIB+constants.convert_to_AB['H'],
                  'K': lambda k: k.MAG_CALIB+constants.convert_to_AB['K'],

                  'g_err': lambda k: k.MAG_PSF_ERR if k.MAG_PSF_ERR else k.MAG_CALIB_ERR,
                  'r_err': lambda k: k.MAG_PSF_ERR if k.MAG_PSF_ERR else k.MAG_CALIB_ERR,
                  'i_err': lambda k: k.MAG_PSF_ERR if k.MAG_PSF_ERR else k.MAG_CALIB_ERR,
                  'z_err': lambda k: k.MAG_PSF_ERR if k.MAG_PSF_ERR else k.MAG_CALIB_ERR,
                  'J_err': lambda k: k.MAG_CALIB_ERR,
                  'H_err': lambda k: k.MAG_CALIB_ERR,
                  'K_err': lambda k: k.MAG_CALIB_ERR,
                  }
    source_data = []
    for OB in set(OBs):
      source_data.append( dict([(k,'') for k in userColumns]) )
      for r in results.filter(imageheader__OB=OB):
        D = {}
        D['ownership'] = {}
        D['ownership'][r.BAND] = r.user.username
        D['imageheader'] = r.imageheader
        for column in userColumns:
          if column not in magnitude_kws:
            D[column] = translation[column](r)
        if r.BAND in userColumns:
          D[r.BAND] = '%0.2f' % translation[r.BAND](r)
          D[r.BAND+"_err"] = '%0.2f' % translation[r.BAND+"_err"](r)
        source_data[-1].update(D)

    #Take care of the possibilty that an imageheader exists where there are no detections of this source 
    allImages = ImageHeader.objects.positionFilter(r.astrosource.RA,r.astrosource.DEC,radius=10,units="arcminutes")
    for (TARGETID,OB,OBTYPEID) in set(zip([i.TARGETID for i in allImages],[i.OB for i in allImages],[i.OBTYPEID for i in allImages])):
      if (TARGETID,OB) not in zip(TARGETIDs,OBs):
        source_data.append( dict([(k,'') for k in userColumns]) )
        D = {}
        D['targetID'] = TARGETID
        D['OBname'] = OB
        D['OBtype'] = OBTYPEID
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
    imageheaders = ImageHeader.objects.getBestImages(
        results[0].astrosource.RA,
        results[0].astrosource.DEC,
        forceOB=nominalOB[0].imageheader.OB,
        )
    return render(request,self.template_name,{'source_data':source_data,'request':request,
                                          'lightcurve':lightcurve[bestBand],'nominalOB':nominalOB,
                                          'SED':SED,'userColumns':userColumns,'lc_band':bestBand,
                                          'imageheaders':imageheaders,
                                          })

  def post(self,request,*args,**kwargs):
    pass
  
