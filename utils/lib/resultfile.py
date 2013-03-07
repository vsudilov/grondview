class ResultFile:
  '''
Defines the ResultFile class. Must be initialized with a path pointing to a GP resultfile, 
ie results['r'] = ResultFile('r/GROND_r_OB_ana.results'). Parses the resultfile header 
using matchstrings and regular expressions. Any change in the formatting of the GP resultfile 
could easily break this. Fortunately, fixing this is quite easy - take a look at the 
structure of _parseRules in __init__(). Also, the columns are hardcoded in.
  
  Attributes:
   headerKeywords [list]     - The keywords that cooresponding to the values 
                               in the result file header
   header [dict]             - headerKeyword:value dictionary list
   objects [list of dicts]   - Dictionary containing ObjID:{column:value}, 
                               for all entries in the resultfile. 
                               ObjID is just the running obj number (integer)
  Methods:
    getNearbyObjs(ra,dec,limit=1)
      Returns a dict of <limit> objects cooresponding to closest 
      sources to the given coordinates. Additionally appends 'DISTANCE':value 
      to the output dictionary
   
   writeRegionFile(objID,output='out.reg',radius='2"',text=None,color='yellow')
     Writes a ds9 region file for that object
   
   dumpRegionFile(output='out.reg',text=None,color='yellow',photo_type=None) 
     dumps the entire resultfile to a ds9 region file
   
   
   Examples:
    1) Find the SED in grizJHK of one object @ ra=20,dec=10
    
      from resultfile import ResultFile
      sed = {}
      for band in ['g','r','i','z','J','H','K']:
        rf = ResultFile('%s/GROND_%s_OB_ana.result' % (band,band))
        objID = rf.getNearbyObjs(20,10).keys()[0]
        magnitude = rf.objects[objID]['MAG_CALIB']
        sed[band] = magnitude
  
    2) Find the seeing and observation time in a series of images (band not important here, of course)

      from resultfile import ResultFile
      OBs = ['OB1_2','OB1_3','OB2_1','OB2_3']
      times = []
      seeings = []
      for OB in OBs:
        rf = ResultFile('%s/r/GROND_r_OB_ana.result' % OB)
        times.append(rf.header['OBS_TIME_MIDTIME'])
        seeings.append(rf.header['SEEING'])
  '''
  def dumpRegionFile(self,output='out.reg',text=None,color='yellow',photo_type=None,font="times 10 bold"):
    fp = open(output,'w')
    for obj in self.objects:
      RA = obj['RA']
      DEC = obj['DEC']
      towrite = 'fk5; circle(%s,%s,0.5") # color=%s' % (RA,DEC,color)
      if photo_type and photo_type not in ["MAG_PSF","MAG_KRON","MAG_APP","MAG_CALIB"]:
        print 'UNKNOWN PHOTO_TYPE: %s' % photo_type
        raise SystemExit
      mag = obj[photo_type]
      mag_err = obj[photo_type+"_ERR"]
      if mag == "INDEF":
        mag = -99
      if mag_err == "INDEF":
        mag_err = -99
          
      if text:
        towrite += ' text={%s (%0.3f,%0.3f) %0.3f +- %0.3f} font={%s}' % (text,RA,DEC,mag,mag_err,font)
      else:
        towrite += ' text={(%0.3f,%0.3f) %0.3f +- %0.3f} font={%s}' % (RA,DEC,mag,mag_err,font)
      towrite += '\n'
      fp.write(towrite)
    fp.close()
    
  def writeRegionfile(self,objID,output='out.reg',radius='2"',text=None,color='yellow'):
    ra = self.objects[objID]['RA']
    dec = self.objects[objID]['DEC']
    if not text:
      line = 'fk5; circle(%s,%s,%s) # color=%s' % (ra,dec,radius,color)
    else:
      line = 'fk5; circle(%s,%s,%s") # color=%s text={%s}' % (ra,dec,radius,color,text)
    fp = open(output,'w')
    fp.write(line)
    fp.close()
    
  def getNearbyObjs(self,ra,dec,limit=1,approx=False):
    '''
    Returns a dictionary of the following form:
    
    foo = resultFile.getNearestObjs(ra,dec,limit=2)
    
    print foo
     --> {objID#1:{'DISTANCE',value,'RA':value,'DEC':value,'MAG_ZEROPOINT':value,...etc,etc...},
         objID#2:{'DISTANCE',:value,'RA':value,'DEC':value,'MAG_ZEROPOINT':value,...etc,etc...}}
    
    print foo.keys()
     --> [objID#1,objID#2]
    
    print foo[objID#1]['DISTANCE']
     --> 0.52      #result is distance in arcseconds
    
    '''
    def arclength(target_ra,target_dec,entry_ra,entry_dec,approx=False):
      #assumes decimal notation for ra,dec. Returns result in arcseconds
      
      if approx:
        return ((target_ra-entry_ra)**2+(target_dec-entry_dec)**2)**(1/2.) * (3600.)
      
      from math import cos, sin, acos, degrees, radians
      arclen = cos(radians(90-target_dec))*cos(radians(90-entry_dec)) 
      arclen += sin(radians(90-target_dec))*sin(radians(90-entry_dec))*cos(radians(target_ra-entry_ra))
      arclen = acos(arclen)
      arclen = degrees(arclen)
      return abs(arclen*60.*60.)
    
    distances = []
    for obj in self.objects:
      distance = arclength(ra,dec,obj['RA'],obj['DEC'],approx=approx)
      distances.append((obj['ObjID'],distance))
    
    distances = sorted(distances,key=lambda k: k[1])
    distances = distances[0:limit]
    
    results = {}
    for entry in distances:
      dist = entry[1]
      objID = entry[0]
      for obj in self.objects:
        if obj['ObjID'] == objID:
          results[objID] = obj
          break
      results[objID].update({'DISTANCE':dist})
    return results
  
  def __init__(self,file_):
    import re
    
    #header attribute: resultFile.header{'KEYWORD':value}
    self.header = {}
        
    #objects attribute: resultFile.objects{objID:{'RA':value,'DEC':value,'MAG_ZEROPOINT':value,...etc,etc}
    self.objects = []
    
    _parseRules = {
        'PIPELINE_VERSION':   {'matchString':   '# GROND MANUAL ANALYSIS PIPELINE',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},
          
        'BAND':     {'matchString':    '-band observation of ',
        'parse':    lambda line: re.search('\D-band',line).group()[0]},
            
        'TARGET':   {'matchString':    '-band observation of ',
        'parse':    lambda line: re.search('of .+',line).group()[3:]},

        'POINTING_RA':    {'matchString':    'Central Pointing ',
        'parse':    lambda line: float(re.search('\d+.\d+').group())},

        'POINTING_DEC':   {'matchString':    'Central Pointing ',
        'parse':    lambda line: float(re.search('\d+.\d+').group())},

        'CATALOG_ASTRO':    {'matchString':    'Catalog used for astrometry',
        'parse':    lambda line: re.search(': .+',line).group()[2:]},

        'CATALOG_CALIB':    {'matchString':    'Catalog used for calibration',
        'parse':    lambda line: re.search(': .+',line).group()[2:]},

        'OB_TYPE':      {'matchString':    'OB type',
        'parse':    lambda line: re.search(': .+',line).group()[2:]},

        'OB_RUNID':      {'matchString':    'Observation run ID',
        'parse':    lambda line: int(re.search('\d+',line).group())},

        'OB_RUNID_SEQUENCE':  {'matchString':    'Observation block sequence number',
        'parse':    lambda line: int(re.search('\d+',line).group())},

        'OBS_TIME_START':    {'matchString':    'Start of the observation in MJD',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'OBS_TIME_MIDTIME':    {'matchString':    'Midtime of the observation in MJD',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'ERROR_TIME_OB':    {'matchString':    'Error of the OB',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'INT_TIME_TOTAL':    {'matchString':    'Total integration time of the image',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'INT_TIME_INDIV':    {'matchString':    'Integration of the individual images',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'MIDTIME_TDP':    {'matchString':    'Midtime of the TDP in MJD',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'ERROR_TIME_TDP':    {'matchString':    'Error of the TDP',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'NUM_IMAGES_COMBINED':   {'matchString':    'Number of images combined',
        'parse':    lambda line: int(re.search('\d+',line).group())},

        'VEGA_AB_CORRECTION':  {'matchString':    'Correction from Vega to AB magnitudes',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'APERTURE_SIZE_PIX':  {'matchString':    'Aperture size is',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'APERTURE_SIZE_ARCSEC':  {'matchString':    'Aperture size is',
        'parse':    lambda line: float(re.search('is \d+.\d+',line).group()[3:])},

        'LIMITING_MAG_3SIG_ZP':  {'matchString':    '3.0s limiting magnitude using zeropoint',
        'parse':    lambda line: float(re.search(': \d+.\d+',line).group()[2:])},

        'LIMITING_MAG_3SIG_CALIB':  {'matchString':    '3.0s limiting magnitude against objects match proximity',
        'parse':    lambda line: float(re.search(': \d+.\d+',line).group()[2:])},

        'LIMITING_MAG_3SIG_CALIB_AB':{'matchString':  '3.0s limiting AB magnitude against objects match proximity',
        'parse':    lambda line: float(re.search(': \d+.\d+',line).group()[2:])},

        'ASTRO_SOLN_ACCURACY_RA':  {'matchString':    'Astrometric solution accuracy in',
        'parse':    lambda line: float(re.search('RA \d+.\d+',line).group()[3:])},

        'ASTRO_SOLN_ACCURACY_DEC':  {'matchString':    'Astrometric solution accuracy in',
        'parse':     lambda line: float(re.search('DEC \d+.\d+',line).group()[4:])},

        'MEAN_FWHM_PIXEL':    {'matchString':    'Mean fwhm of stars',
        'parse':    lambda line: float(re.search(': \d+.\d+',line).group()[3:])},

        'MEAN_FWHM_ARCSEC':    {'matchString':    'Mean fwhm of stars',
        'parse':    lambda line: float(re.search(', \d+.\d+',line).group()[3:])},

        'MEAN_AIRMASS':    {'matchString':    'Mean airmass',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'EXTINCTION_COEFF':    {'matchString':    'Extinction coefficient',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'CALIB_CHI2':    {'matchString':    'Calibration against objects match proximity',
        'parse':    lambda line: float(re.search('= \d+.\d+',line).group()[2:])},

        'ZEROPOINT_AIRMASS1':  {'matchString':    'Zeropoint against objects match proximity',
        'parse':    lambda line: getZP_1(line)},

        'ZEROPOINT_EFFECTIVE':  {'matchString':    'Zeropoint against objects match proximity',
        'parse':    lambda line: getZP_eff(line)},

        'CALIB_RMS':          {'matchString':    'Calibration rms scatter against objects match proximity',
        'parse':    lambda line: float(re.search('\d+.\d+',line).group())},

        'XYXYMATCH_FAILURE':   {'matchString':    'XYXYmatch failed',
        'parse':            lambda line: True},

        'KRON_CORRECTION':    {'matchString': 'Kron magnitude correction to iraf:',
        'parse':            lambda line: float(re.search('\d+.\d+',line).group())}
    
    }
    
    self.headerKeywords = _parseRules.keys()
    
    def getZP_eff(line): #helper function to parse the zeropoints @ different arbitrary airmasses
      if self.header.has_key('ZEROPOINT_EFFECTIVE') and self.header['ZEROPOINT_EFFECTIVE']:
        return self.header['ZEROPOINT_EFFECTIVE']
      
      if re.search('airmass \d+.\d+',line):
        return float(re.search(': \d+.\d+',line).group()[2:])
      else:
        return None
    
    def getZP_1(line): #helper function to parse the zeropoints @ different arbitrary airmasses
      if self.header.has_key('ZEROPOINT_AIRMASS1') and self.header['ZEROPOINT_AIRMASS1']:
        return self.header['ZEROPOINT_AIRMASS1']
      if re.search('airmass \d+',line) and not re.search('airmass \d+.\d+',line):
        return float(re.search(': \d+.\d+',line).group()[2:])
      else:
        return None

      
    
    columns = {}
    columns['RA'] = 0
    columns['DEC'] = 1
    columns['MAG_PSF'] = 2
    columns['MAG_PSF_ERR'] = 3
    columns['MAG_APP'] = 4
    columns['MAG_APP_ERR'] = 5
    columns['MAG_KRON'] = 6
    columns['MAG_KRON_ERR'] = 7
    columns['OFFSET_ASTRO'] = 8
    columns['OFFSET_ALL'] = 9
    columns['OFFSET_ASTRO_ERR'] = 10
    columns['OFFSET_ALL_ERR'] = 11
    columns['MAG_CALIB'] = 12
    columns['MAG_CALIB_ERR'] = 13
    columns['ELONGATION'] = 14
    columns['R_HALFLIGHT'] = 15
    columns['CLASS_STAR'] = 16
    
    fp = open(file_,'r')
    objID = -1
    for line in fp:
      if not line: 
        continue
      if line.startswith('#'):
        for keyword in _parseRules:
          if _parseRules[keyword]['matchString'] in line:
            try:
              self.header[keyword] = _parseRules[keyword]['parse'](line)
            except:
              print '*** WARNING FAILED PARSE ***'
              print _parseRules[keyword]['matchString']
              print line
              print '****************************'
        continue
      line = line.split()
      obj = {}
      objID += 1
      for keyword in columns.keys():
        try:
          obj[keyword] = float(line[columns[keyword]])
        except ValueError: #Take care of INDEF entries
          obj[keyword] = line[columns[keyword]]
      obj['ObjID'] = objID
      self.objects.append(obj)
    if not self.header.has_key('XYXYMATCH_FAILURE'):
      self.header['XYXYMATCH_FAILURE'] = False
