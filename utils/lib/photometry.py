import sys,os

from pyraf import iraf    # You MUST HAVE this line first.
from iraf import digiphot # noao.digiphot
from iraf import apphot   # noao.digiphot.apphot (daofind, phot, txdump)
from iraf import daophot  # noao.digiphot.daophot(pstselect, allstar, psf)
from iraf import imcoords

import numpy as np

try:
  from grondview.settings import PROJECT_ROOT
  from grondview.settings import MEDIA_ROOT
except ImportError:
  PROJECT_ROOT = '/home/vagrant/grondview/' #For running seperately on sauron (not precise64.box), debug ONLY
  MEDIA_ROOT = '/home/vagrant/grondview/media/'
import constants

import sextractor
import pyfits

import time
import numpy as np
import ConfigParser
import logging

PLOT=False

PHOTO_TOLERANCE = dict( (b,0.2) for b in 'griz' )
PHOTO_TOLERANCE.update( dict( (b,0.3) for b in 'JHK'))

if PLOT:
  import matplotlib
  matplotlib.use('Agg')
  from matplotlib import pyplot as plt


def makeSexConfig(sex, task, **kwargs):

  sex.config['CATALOG_NAME'] = os.path.join(task['output_directory'],'sextractor.cat')
  sex.config['CATALOG_TYPE'] = 'ASCII_HEAD'
  sex.config['PARAMETERS_NAME'] = "default.param"

  sex.config['DETECT_TYPE'] = 'CCD'

  detect_thresh = 10 if task['band'] in constants.optical else 7
  detect_minarea = 10 if task['band'] in constants.optical else 7
    
  sex.config['DETECT_MINAREA'] = detect_minarea
  sex.config['DETECT_THRESH'] = detect_thresh #sigma about RMS background

  sex.config['FILTER'] = 'N'

  sex.config['DEBLEND_NTHRESH'] = 32
  sex.config['DEBLEND_MINCONT'] = 0.1 #Spit into objects if branch contains X% of the flux from total

  sex.config['BACK_VALUE'] = 0
  sex.config['BACK_TYPE'] = 'MANUAL'

  sex.config['CHECKIMAGE_TYPE'] = ''
  sex.config['CHECKIMAGE_NAME'] = ''
  
  sex.config['MEMORY_OBJSTACK'] = 3000
  sex.config['MEMORY_PIXSTACK'] = 300000
  sex.config['MEMORY_BUFSIZE'] = 1024

  sex.config['PARAMETERS_LIST'] = []
  sex.config['PARAMETERS_LIST'].append('ALPHA_J2000')
  sex.config['PARAMETERS_LIST'].append('DELTA_J2000')
  sex.config['PARAMETERS_LIST'].append('X_IMAGE')
  sex.config['PARAMETERS_LIST'].append('Y_IMAGE')
  sex.config['PARAMETERS_LIST'].append('FWHM_IMAGE')
  if kwargs:
    for key in kwargs:
      sex.config[key] = kwargs[key]


def performPhotometry(task, logger):
  #iraf.prcacheOff()
  [iraf.unlearn(t) for t in ('phot','pstselect','psf','allstar')]
  iraf.set(imtype="fits,noinherit")   # set image output format
  iraf.set(clobber="yes")
  hdu=pyfits.open(task['images'])[0] 
  hdr = hdu.header
  imdata = hdu.data  
  for key,value in task['fits'].iteritems():
    task[key] = hdr.get(value,1)

  #Sextractor to find stars; add an object for the force detect
  logger.info('Running SExtractor on [%s]' % os.path.basename(task['images']))
  sex = sextractor.SExtractor()
  makeSexConfig(sex,task)
  sex.run(task['images'],path=task['sexpath'])
  catalog = sex.catalog()

  #Set up image parameters
  MIN_X = max(1,int(task['numpixx']*task['filtfactor']))
  MIN_Y = max(1,int(task['numpixy']*task['filtfactor']))
  MAX_X = int(task['numpixx']*(1-task['filtfactor']))
  MAX_Y = int(task['numpixy']*(1-task['filtfactor']))
  AREAXY = '[%s:%s,%s:%s]' % (MIN_X, MAX_X, MIN_Y, MAX_Y)
  AREANO = '[%s:%s,%s:%s]' % (MIN_X, MAX_X-2*MIN_X, MIN_Y, MAX_Y-2*MIN_Y)
  try:
    task['pixscale'] = abs(hdr.get('CD1_1'))*3600.
  except TypeError:
    task['pixscale'] = abs(hdr.get('CDELT1'))*3600.
  task['seeing'] = np.median( sorted([i['FWHM_IMAGE'] for i in catalog])[:int(-len(catalog)*0.5)] ) #Take the median of the "bottom" 50% of objects
  
  logger.info('--> %s SExtractor detected bright objects in the field' % (len(catalog),) )
  logger.info('--> %0.2f median FWHM of bright objects in the field, in arcsec' % (task['seeing']*task['pixscale'],))

  task['objects'] = [(i['ALPHA_J2000'],i['DELTA_J2000']) for i in catalog]
  task['objects'].append(task['objwcs'])  
  task['objectlist'] = open(os.path.join(task['output_directory'],'objectlist'),'w')  
  task['objectlist'].write('\n'.join([' %s %s' % (i[0],i[1]) for i in task['objects']]))
  task['objectlist'].close()

  logger.info('Running iraf.imstat')
  irafoutput = iraf.imstat(images=task['images']+AREANO,fields='midpt,min,max,stddev', format=0, Stdout=1)
  task['nimgs'] = hdr.get('NIMGS',1)
  task['gain'] *= task['nimgs']*2/3.
  task['ron'] *= np.sqrt(task['nimgs'])/task['nimgs']*constants.INTERPSM[task['band']]
  task['datamean'], task['datamin'], task['datamax'], task['datastdev']  = map(float, irafoutput[0].split())
  irafoutput = iraf.imstat(images=task['images'],fields='stddev,midpt',nclip=25,format=0,cache='yes',Stdout=1)
  task['skynoise'], task['datamean'] = map(float, irafoutput[0].split() )
  task['skynoise'] *= constants.INTERPSM[task['band']]
  task['airmass'] = hdr.get('AIRMASS',1)
  task['zmag'] -= (float(task['airmass'])-1.0)*constants.extinction_coefficients[task['band']]  
  task['match_proximity'] = 2.5 * task['seeing']
  logger.info('--> %5.2f counts: Sky noise, corrected for drizzle imcombine' % task['skynoise'])
  logger.info('--> %5.2f Median count value, after background subtraction' % task['datamean'])
  logger.info('--> %5.2f Airmass' % task['airmass'])

  #prepare temp files that iraf will use
  for filename in ('photfile','pstfile','psfimg','opstfile','groupfile','allstarfile','rejfile','subimage'): 
    task[filename] = open(os.path.join(task['output_directory'],filename),'w')
    task[filename].close()

  #iraf.phot to get APP magnitudes
  logger.info('Running iraf.apphot.phot')
  #apsizes = [i*task['faperture']*task['seeing'] for i in (0.4,0.5,0.6,0.8,1.0,1.2,1.5,2.0,2.5,3.0)]
  #irafapsizes = ','.join(['%.2f' % i for i in apsizes])
  irafapsizes = '%0.2f' % (task['faperture']*task['seeing'])
  kwargs = dict(image=task['images'],coords=task['objectlist'].name,
    output=task['photfile'].name,
    interac='no',scale=1,
    fwhmpsf=task['seeing'], 
    wcsin='world', wcsout='physical',
    sigma=task['skynoise'],
    datamin=task['datamin'],
    datamax=task['datamax'],
    readnoi=task['ron'],
    epadu=task['gain'],
    itime=task['exposure'],
    xairmass=task['airmass'],
    ifilter=task['band'],
    otime=task['dateobs'],
    aperture= irafapsizes,
    zmag=task['zmag'],
    annulus=task['fannulus']*task['seeing'],
    dannulus=task['fdannulus']*task['seeing'],
    calgorithm='gauss',
    cbox = 1.5*task['seeing'],
    maxshift=15,
    mode="h",Stdout=1,verify=0)
  iraf.phot(**kwargs)

  #iraf.pstselect to choose objects for PSF modelling
  logger.info('Running iraf.daophot.pstselect')
  kwargs = dict(image=task['images'],
                   photfile=task['photfile'].name,pstfile=task['pstfile'].name,
                   maxnpsf=task['pstnumber'],
                   wcsin='physical',
                   wcsout='physical',
                   interac="no",verify='no',scale=1,
                   fwhmpsf=task['seeing'],
                   datamin=0,
                   datamax=task['datamax'],
                   psfrad=3.0*task['seeing'],
                   fitrad=1.0*task['seeing'],
                   recente='yes',
                   nclean=task['nclean'],
                   mode="h",Stdout=1)
  iraf.pstselect(**kwargs)

  #iraf.psf to model PSF
  logger.info('Running iraf.daophot.psf')
  kwargs = dict( image=task['images'],
            photfile=task['photfile'].name,
            pstfile=task['pstfile'].name,
            psfimage=task['psfimg'].name,
            opstfile=task['opstfile'].name,
            groupfile=task['groupfile'].name,
            wcsin='physical',wcsout='physical',
            interac="no",verify="no",scale=1,
            fwhmpsf=task['seeing'],
            sigma=task['skynoise'],
            datamin=task['datamin'],
            datamax=task['datamax'],
            readnoi=task['ron'],
            epadu=task['gain'],
            itime=task['exposure'],
            xairmass=task['airmass'],
            ifilter=task['band'],
            otime=task['dateobs'],
            function=task['func'],
            varorder=task['varorder'],
            saturat='no',
            psfrad=3.0*task['seeing'],
            fitrad=1.*task['faperture']*task['seeing'],
            nclean=task['nclean'],
            mergerad=1.5*task['seeing'],
            mode='h',Stdout=1)  

  iraf.psf(**kwargs)
  logger.info('Running iraf.daophot.allstar')
  #iraf.allstars to compute PSF photometry; recenter with recenter='yes', mergerad=<value> to avoid duplicate detection
  kwargs = dict(image=task['images'],
                photfile=task['photfile'].name,
                wcsin='physical',
                wcsout='physical',
                psfimage=task['psfimg'].name,
                allstarf=task['allstarfile'].name,
                rejfile=task['rejfile'].name,
                subimage=task['subimage'].name,
                verbose=1,verify='no',scale=1,
                fwhmpsf=task['seeing'],
                sigma=task['skynoise'],
                datamin=task['datamin'],
                datamax=task['datamax'],
                readnoi=task['ron'],
                epadu=task['gain'],
                itime=task['exposure'],
                xairmass=task['airmass'],
                ifilter=task['band'],
                otime=task['dateobs'],
                function=task['func'],
                varorder=task['varorder'],
                psfrad=3.*task['seeing'],
                fitrad=1.*task['faperture']*task['seeing'],
                recenter='yes',
                mergerad=1.5*task['seeing'],
                mode='h',Stdout=1)
  iraf.allstar(**kwargs)
  

  #Parse both photometry, convert to RA,DEC,MAG,MAGERR
  logger.info('iraf tasks complete. Parsing results and calibrating')
  photometry = {}
  photometry['APP'] = iraf.txdump(textfiles=task['photfile'].name,
                        fields='XCENTER,YCENTER,MAG,MERR',expr='yes',
                        headers='no',Stdout=1)
  photometry['PSF'] = iraf.txdump(textfiles=task['allstarfile'].name,
                        fields='XCENTER,YCENTER,MAG,MERR',expr='yes',
                        headers='no',Stdout=1)

  for phototype in photometry:
    kwargs = dict(input='STDIN',
                  output='STDOUT',
                  insystem='%s physical' % task['images'],
                  outsystem='%s world' % task['images'],
                  ilatuni='physical',
                  ilnguni='physical',
                  olnguni='degrees',
                  olatuni='degrees',
                  ilngfor='%10.7f',
                  ilatfor='%10.7f',
                  olngfor='%10.5f',
                  olatfor='%10.5f',
                  Stdin=photometry[phototype],Stdout=1)
    photometry[phototype] = [i.split() for i in iraf.skyctran(**kwargs) if i and not i.startswith('#') and 'INDEF' not in i]
    photometry[phototype] = [map(float,(i[4],i[5],i[2],i[3])) for i in photometry[phototype] ] #Now we have [(ra,dec,'mag','mageerr'),...]
  results = calibrate((task['objwcs'][0],task['objwcs'][1]),task,photometry,logger)
  return results

def calibrate(usersource,task,photometry,logger):
  results = {}
  #Find correct calibration catalog
  # Order of preference:
  #  1. calcat=<file> in ?ana.ini
  #  2. 2MASS (JHK), SDSS (griz)
  #  3. No catalog, no calibration (use zeropoints)
  if not os.path.isfile(task['calcat']):
    if task['band'] in constants.infrared:
      task['calcat'] = os.path.join(task['workdir'],'GROND_%s_OB_cat_2MASS.tsv' % task['band'])
    elif task['band'] in constants.optical:
      c = os.path.join(task['workdir'],'GROND_%s_OB_cat_SDSS.tsv' % task['band'])
      if os.path.isfile(c):
        task['calcat'] = c
      else:
        task['calcat'] = 'instrumental zeropoints'
  logger.info('--> Calibrating against [%s]' % os.path.basename(task['calcat']))
  
  def matchsource(ra,dec,catalog):
    #Return catalog [ra,dec,mag,magerr] for the matched source
    distances = [[catsource,constants.arclength(ra,dec,catsource[0],catsource[1])] for catsource in catalog]
    distances = [i for i in distances if i[1]<task['match_proximity']]
    if not distances:
      return None
    distances = sorted(distances,key=lambda k: k[1])[0]
    return distances[0]

  if task['calcat'] == 'instrumental zeropoints':
    for phototype in photometry:
      results[phototype] = matchsource(usersource[0],usersource[1],photometry[phototype])
    return results

  with open(task['calcat'],'r') as f:
    calcat = [map(float,i.strip().split()) for i in f]
  from scipy import optimize #Big import
  fitfunc = lambda p, x: p[0] + p[1] * x #linear fit
  errfunc = lambda p, x, y, err: (y - fitfunc(p, x)) / err
  pinit = [0.0, 1.0]
  results = {}
  for phototype in photometry:
    data = []
    for source in photometry[phototype]:
      matchedsource = matchsource(source[0],source[1],calcat)
      if not matchedsource:
        continue
      if abs(matchedsource[2]-source[2]) > PHOTO_TOLERANCE[task['band']]:
        continue
      data.append( [source[2],matchedsource[2],np.sqrt(source[3]**2+matchedsource[3]**2) ] )
    x = np.array([i[0] for i in data])
    y = np.array([i[1] for i in data])
    yerr = np.array([i[2] for i in data])
    out, covar, inf, mesg, ier = optimize.leastsq(errfunc, pinit, args=(x, y, yerr), full_output=1)
    chi2 = 0
    med = out[0]
    mult = out[1]
    for (xval,yval,yvalerr) in zip(x,y,yerr):
        chi2+=((med+mult*xval-yval)/yvalerr)**2
    dof = len(y)-1
    redchi2 = chi2/dof
    pfinal = out
    logger.info('--> %5.2f reduced chi2 for %s photometry using %s objects' % (redchi2,phototype,len(y)) )    
    if PLOT:
      fig = plt.figure()
      ax = fig.gca()    
      ax.errorbar(x,y,yerr=yerr,fmt='r.')
      line_x = np.linspace(min(x),max(x),100)
      line_y = pfinal[0]+pfinal[1]*line_x
      ax.plot(line_x,line_y,'-')
      plt.savefig('calib-%s.png' % phototype,format='png')
      logger.info('--> Calibration plot [%s] saved' % phototype)
    #Find the user source again, apply calibration
    calibrated_data = [ [i[0],i[1],i[2]*pfinal[1]+pfinal[0],i[3] ] for i in photometry[phototype] ]
    results[phototype] = matchsource(usersource[0],usersource[1],calibrated_data)
  results['zeropoints'] = matchsource(usersource[0],usersource[1],photometry['PSF'])
  #end product: {'APP':[ra,dec,mag,magerr],'PSF':[...],'zeropoints':[...]}
  return results         

def parseIni(iniFile,task):
  cp = ConfigParser.ConfigParser()
  cp.read(iniFile)
  
  #get floats in ini
  s = 'task'
  for param in ('varorder','faperture','fannulus','fdannulus','filtfactor','zmag','nclean','pstnumber'):
   task[param] = cp.getfloat(s,param)
  #get strings in ini
  for param in ('band','func','calcat','workdir',): 
   task[param] = cp.get(s,param)
  task['images'] = os.path.join(task['workdir'],'GROND_%s_OB_ana.fits' % task['band'])
  s = 'fits'
  task[s] = {}
  for param in ('ra','dec','numpixx','numpixy','exposure','dateobs','ron','gain'):
    task[s][param] = cp.get(s,param)

  task['sexpath'] = os.path.join(PROJECT_ROOT,'utils/bin/sex')
  return task


def main(iniFile, logger, objwcs, jobid):
  task = {}
  task['output_directory'] = os.path.join(MEDIA_ROOT,jobid)
  if not os.path.isdir(task['output_directory']):
    os.mkdir(task['output_directory'])
  if not logger:
    logfmt = '%(levelname)s: (%(asctime)s) %(message)s'
    datefmt= '%I:%M:%S %p'
    formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
    logger = logging.getLogger('__main__')
    logging.root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler() #console handler
    ch.setFormatter(formatter)
    fh = logging.FileHandler(filename=open(os.path.join(task['output_directory'],'logfile'),'a').name,mode='a') #file handler
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
  start = time.time()
  logger.info("Starting photometry module.") 
  parseIni(iniFile,task)
  task['objwcs'] = objwcs
  task['jobid'] = jobid
  results = performPhotometry(task,logger)    
  if task['band'] in constants.optical:
    if not results['PSF']:
      logger.warning('PSF photometry failed, reporting APP photometry instead')
      result = results['APP']
    else:
      result = results['PSF']
      logger.info('Reporting results from PSF photometry')
  else:
    result = results['APP']
  if not result:
    logger.critical('Unable to compute photometry for this position!')
    raise Exception, 'No results from photometry'
  logger.info('Reporting results from APP photometry')
  logger.info('Successfully performed photometry for object at ra,dec %0.4f,%0.4f' % (result[0],result[1]))
  for k,v in results.iteritems():
    logger.info("--> [%s]: %5.2f +- %2.2f" % (k,k[v][2],k[v][3]))
  end = time.time()
  logger.info("Photometry completed in %0.1f seconds" % (end-start) ) 
  return result

if __name__=="__main__":
  #For test purposes
  r = main('/home/vagrant/grondview/work/ini/COSMOS03/OB1_1/rana.ini',None,(150.02838, 2.27318),'223j-sa3-ad3-a3sd')
  print r
