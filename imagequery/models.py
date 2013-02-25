from django.db import models
from django.db.models.query import QuerySet
import os
import sys

from grondview.settings import PROJECT_ROOT
sys.path.insert(0,os.path.join(PROJECT_ROOT,'utils'))

from lib import constants

from astLib import astCoords

#--------------------------------------------
#Clever trick to override QuerySets, enabling
#chaining of custom queries:
#Enables model.objects.positionFilter()
#as well as model.objects.filter(FILTER__in=bands).positionFilter(ra,dec,radius)
#http://zmsmith.com/2010/04/using-custom-django-querysets/
class ImageHeaderQuerySet(QuerySet):
  def imagePositionFilter(self,ra,dec,radius,units="arcminutes"):
    """
    Filters a queryset based on arclength. Returns a List of 
    database rows, therefore must be the last piece of a QuerySet chain.
    """
    radius *= constants.convert_arcmin_or_arcsec_to_degrees[units]

    results = []
    for i in self:
      if astCoords.calcAngSepDeg(i.CRVAL1,i.CRVAL2,ra,dec) <= radius:
        results.append(i)
    return results
class ImageHeaderManager(models.Manager):
  def get_query_set(self):
    return ImageHeaderQuerySet(self.model)
  def __getattr__(self, name):
    return getattr(self.get_query_set(), name)
#--------------------------------------------


class ImageHeader(models.Model):
  """
  Defines the django model that stores FITS header info, along with path to that image
  """
  def __unicode__(self):
    return "%s-%s: %s" % (self.TARGETID,self.FILTER,self.PATH)
  #-- Fields
  PATH = models.CharField(max_length=80)
  NAXIS1 = models.IntegerField()
  NAXIS2 = models.IntegerField()
  RA = models.FloatField() #Telescope pointing
  DEC = models.FloatField()
  EXPTIME = models.FloatField()
  MJD_OBS = models.FloatField()
  DATE_OBS = models.CharField(max_length=30)
  CRVAL1 = models.FloatField() #Center of field (astrometry)
  CRVAL2 = models.FloatField()
  NGR = models.IntegerField()
  NINT = models.IntegerField()
  NIZ = models.IntegerField()
  NMD = models.IntegerField()
  NTD = models.IntegerField()
  NTP = models.IntegerField()
  OBSEQNUM = models.IntegerField()
  OBSRUNID = models.IntegerField()
  TARGETID = models.CharField(max_length=40)
  FILTER = models.CharField(max_length=1)
  RON = models.FloatField()
  GAIN = models.FloatField()
  MJD_MID = models.FloatField()
  OBSERR = models.FloatField()
  NCOMBINE = models.IntegerField()
  NIMGS = models.IntegerField()
  TDP_MID = models.FloatField()
  INTERPSM = models.FloatField()
  AIRMASS = models.FloatField()
  IMGEXP = models.FloatField()
  
  #-- Manager
  objects = ImageHeaderManager()










#SIMPLE  =                    T / Fits standard
#BITPIX  =                  -32 / Bits per pixel
#NAXIS   =                    2 / Number of axes
#NAXIS1  =                 1906 / Axis length
#NAXIS2  =                 1906 / Axis length
#EXTEND  =                    T / File may contain extensions
#ORIGIN  = 'NOAO-IRAF FITS Image Kernel July 2003' / FITS file originator
#IRAF-TLM= '2012-12-04T09:56:31' / Time of last modification
#DATE    = '2012-12-04T09:56:23' / Date the file was written
#TELESCOP= 'MPI-2.2 '                    / ESO Telescope Name
#INSTRUME= 'GROND   '                    / Instrument used.
#OBJECT  = '        '           / Original target.
#RA      =           289.240218 / 19:16:57.6 RA (J2000) at start in (deg
#DEC     =               5.1509 / 05:09:03.2 DEC (J2000) at start in (de
#EQUINOX =                2000. / Standard FK5 (years)
#RADECSYS= 'FK5     '           / Coordinate reference frame
#EXPTIME =            2.0000000 / Integration time
#MJD-OBS =       55852.00467373 / Obs start 2011-10-18T00:06:43.811
#DATE-OBS= '2011-10-18T00:06:43.8107' / Observing date
#UTC     =              400.132          / 00:06:40.132 UTC at start (sec)
#LST     =            76097.395          / 21:08:17.395 LST at start (sec)
#PI-COI  = 'Greiner '           / PI-COI name.
#CTYPE1  = 'RA---TAN'           / Coordinate type.
#CTYPE2  = 'DEC--TAN'           / Coordinate type.
#CRVAL1  =     289.245232736568 / WCS RA.
#CRVAL2  =     5.14325703721099 / WCS DEC.
#ORIGFILE= 'GROND_IRIM.291_0001.fits' / Original File Name
#AUTO    =                    F          / Pipeline generated OB.
#CGR     =                    1          / GR frame number per tel. pos..
#CINT    =                    1          / Frames per mirror position.
#CIZ     =                    1          / IZ frames number per tel. pos..
#CMD     =                    1          / Cur mirror position.
#CMP     =                    1          / Cur mirror dithering.
#CTD     =                    1          / Current tel position.
#CTP     =                    1          / Current tel dithering.
#CUNIT1  = 'deg     '           / Coordinate unit.
#CUNIT2  = 'deg     '           / Coordinate unit.
#DEC2000 =               5.1509 / Telescope pointing.
#HIERARCH ESO ADA GUID STATUS = 'OFF     '   / Status of autoguider
#HIERARCH ESO ADA POSANG      =      0.90000 / Position angle at start
#HIERARCH ESO DET CHIP ID     = 'ESO-Hawaii' / Detector ID
#HIERARCH ESO DET CHIP NAME   = 'Hawaii' / Detector name
#HIERARCH ESO DET CHIP NX     = 3072 / Pixels in X
#HIERARCH ESO DET CHIP NY     = 1024 / Pixels in Y
#HIERARCH ESO DET CHIP PXSPACE= 1.800e-05 / Pixel-Pixel Spacing
#HIERARCH ESO DET CHIP TYPE   = 'IR' / The Type of Det Chip
#HIERARCH ESO DET CHOP FREQ   = 0 / Chopping Frequency
#HIERARCH ESO DET CON OPMODE  = 'NORMAL' / Operational Mode
#HIERARCH ESO DET DID         = 'ESO-VLT-DIC.IRACE-1.33' / Dictionary Name and Re
#HIERARCH ESO DET DIT         = 2.0000000 / Integration Time
#HIERARCH ESO DET DITDELAY    = 0.100 / Pause Between DITs
#HIERARCH ESO DET EXP NAME    = 'GROND_IRIM.291_0001' / Exposure Name
#HIERARCH ESO DET EXP NO      = 10266 / Exposure number
#HIERARCH ESO DET EXP UTC     = '2011-10-18T00:06:48.2243' / File Creation Time
#HIERARCH ESO DET FRAM NO     = 1 / Frame number
#HIERARCH ESO DET FRAM TYPE   = 'INT' / Frame type
#HIERARCH ESO DET FRAM UTC    = '2011-10-18T00:06:47.9463' / Time Recv Frame
#HIERARCH ESO DET IRACE ADC1 DELAY= 4 / ADC Delay Adjustment
#HIERARCH ESO DET IRACE ADC1 ENABLE= 1 / Enable ADC Board (0/1)
#HIERARCH ESO DET IRACE ADC1 FILTER1= 0 / ADC Filter1 Adjustment
#HIERARCH ESO DET IRACE ADC1 FILTER2= 0 / ADC Filter2 Adjustment
#HIERARCH ESO DET IRACE ADC1 HEADER= 1 / Header of ADC Board
#HIERARCH ESO DET IRACE ADC1 NAME= 'ADC-16' / Name for ADC Board
#HIERARCH ESO DET IRACE SEQCONT= 'F' / Sequencer Continuous Mode
#HIERARCH ESO DET MODE NAME   = 'DoubleCorr' / DCS Detector Mode
#HIERARCH ESO DET NCORRS      = 2 / Read-Out Mode
#HIERARCH ESO DET NCORRS NAME = 'Double' / Read-Out Mode Name
#HIERARCH ESO DET NDIT        = 1 / # of Sub-Integrations
#HIERARCH ESO DET NDITSKIP    = 0 / DITs skipped at 1st.INT
#HIERARCH ESO DET RSPEED      = 6 / Read-Speed Factor
#HIERARCH ESO DET RSPEEDADD   = 0 / Read-Speed Add
#HIERARCH ESO DET WIN NX      = 3072 / # of Pixels in X
#HIERARCH ESO DET WIN NY      = 1024 / # of Pixels in Y
#HIERARCH ESO DET WIN STARTX  = 1 / Lower left X ref
#HIERARCH ESO DET WIN STARTY  = 1 / Lower left Y ref
#HIERARCH ESO DET WIN TYPE    = 0 / Win-Type: 0=SW/1=HW
#HIERARCH ESO DPR CATG        = 'SCIENCE '   / Observation category
#HIERARCH ESO DPR TECH        = 'IMAGE   '   / Observation technique
#HIERARCH ESO DPR TYPE        = 'OBJECT  '   / Observation type
#HIERARCH ESO INS DATE        = '2000-06-16' / Instrument release date (yyyy-mm-d
#HIERARCH ESO INS MODE        = 'IMAGING '   / Instrument mode used.
#HIERARCH ESO OBS DID         = 'ESO-VLT-DIC.OBS-1.11' / OBS Dictionary
#HIERARCH ESO OBS GRP         = '0       '   / linked blocks
#HIERARCH ESO OBS ID          =           -1 / Observation block ID
#HIERARCH ESO OBS NAME        = '4min4TD '   / OB name
#HIERARCH ESO OBS PI-COI ID   =            0 / ESO internal PI-COI ID
#HIERARCH ESO OBS PI-COI NAME = 'Greiner '   / PI-COI name
#HIERARCH ESO OBS PROG ID     = '087.A-9099(A)' / ESO program identification
#HIERARCH ESO OBS START       = '2011-10-18T00:04:52' / OB start time
#HIERARCH ESO OBS TPLNO       =            2 / Template number within OB
#HIERARCH ESO OCS DET1 IMGNAME= 'GROND_IRIM.' / Data File Name.
#HIERARCH ESO TEL AG FIBSELEC = 'OBJFIB  '   / Fiber currently used (SKY or OBJ)
#HIERARCH ESO TEL AG FIBX     =        0.000 / Fiber position X
#HIERARCH ESO TEL AG FIBY     =        0.000 / Fiber position Y
#HIERARCH ESO TEL AG REFX     =      822.493 / Autoguider reference pixel X
#HIERARCH ESO TEL AG REFY     =      516.328 / Autoguider reference pixel Y
#HIERARCH ESO TEL AIRM END = 1.379 / Airmass at end
#HIERARCH ESO TEL AIRM START = 1.377 / Airmass at start
#HIERARCH ESO TEL ALT         =       46.518 / Alt angle at start (deg)
#HIERARCH ESO TEL AMBI FWHM END=        1.26 / Observatory Seeing queried from AS
#HIERARCH ESO TEL AMBI FWHM START=      1.26 / Observatory Seeing queried from AS
#HIERARCH ESO TEL AMBI PRES END=      770.10 / Observatory ambient air pressure q
#HIERARCH ESO TEL AMBI PRES START=    770.10 / Observatory ambient air pressure q
#HIERARCH ESO TEL AMBI RHUM   =           37. / Observatory ambient relative humi
#HIERARCH ESO TEL AMBI TEMP   =         9.20 / Observatory ambient temperature qu
#HIERARCH ESO TEL AMBI WINDDIR=           34. / Observatory ambient wind directio
#HIERARCH ESO TEL AMBI WINDSP =         4.60 / Observatory ambient wind speed que
#HIERARCH ESO TEL AZ          =      137.745 / Az angle at start (deg) S=0,W=90
#HIERARCH ESO TEL CHOP ST     =            F / True when chopping is active
#HIERARCH ESO TEL DATE        = '2000-10-15T15:21:35.745' / TCS installation date
#HIERARCH ESO TEL DID         = 'ESO-2P2-DIC.TCS-1.8' / Data dictionary for TEL
#HIERARCH ESO TEL DOME STATUS = 'FULLY-OPEN' / Dome status
#HIERARCH ESO TEL FOCU ID     = 'CA      '   / Telescope focus station ID
#HIERARCH ESO TEL FOCU LEN    =        8.009 / Focal length (m)
#HIERARCH ESO TEL FOCU SCALE  =       11.650 / Focal scale (arcsec/mm)
#HIERARCH ESO TEL FOCU VALUE  =    22913.000 / M2 setting (mm)
#HIERARCH ESO TEL GEOELEV     =         2335. / Elevation above sea level (m)
#HIERARCH ESO TEL GEOLAT      =     -29.2543 / Tel geo latitute (+=North) (deg)
#HIERARCH ESO TEL GEOLON      =     -70.7346 / Tel geo longitute (+=East) (deg)
#HIERARCH ESO TEL HSS HUMI1 END=      43.700 / outside south of dome in shadow
#HIERARCH ESO TEL HSS HUMI1 START=    43.770 / outside south of dome in shadow
#HIERARCH ESO TEL HSS HUMI2 END=      41.210 / inside dome midheight
#HIERARCH ESO TEL HSS HUMI2 START=    41.900 / inside dome midheight
#HIERARCH ESO TEL ID          = 'v 5.19+ '   / TCS version number
#HIERARCH ESO TEL MOON DEC    =     22.41698 / 22:25:01.1 DEC (J2000) (deg)
#HIERARCH ESO TEL MOON DIST   =    146.49631 / Moon distance to target
#HIERARCH ESO TEL MOON RA     =    89.776989 / 05:59:06.4 RA (J2000) (deg)
#HIERARCH ESO TEL OPER        = 'I: Condor'  / Telescope Operator
#HIERARCH ESO TEL PARANG END  =      143.880 / Parallactic angle at end (deg)
#HIERARCH ESO TEL PARANG START=      143.911 / Parallactic angle at start (deg)
#HIERARCH ESO TEL TARG ALPHA  =   191657.600 / Alpha coordinate for the target
#HIERARCH ESO TEL TARG DELTA  =    50902.000 / Delta coordinate for the target
#HIERARCH ESO TEL TARG EPOCH  =     2000.000 / Epoch
#HIERARCH ESO TEL TARG EPOCHSYSTEM= 'J       ' / Epoch system (default J=Julian)
#HIERARCH ESO TEL TARG EQUINOX=     2000.000 / Equinox
#HIERARCH ESO TEL TARG PMA    =     0.000000 / Proper Motion Alpha
#HIERARCH ESO TEL TARG PMD    =     0.000000 / Proper motion Delta
#HIERARCH ESO TEL TRAK RATEA  =    15.000000 / Tracking rate in RA (arcsec/sec)
#HIERARCH ESO TEL TRAK RATED  =     0.000000 / Tracking rate in DEC (arcsec/sec)
#HIERARCH ESO TEL TRAK STATUS = 'NORMAL  '   / Tracking status
#HIERARCH ESO TEL TSS TEMP1 END=       9.200 / air outside south of dome in shado
#HIERARCH ESO TEL TSS TEMP1 START=     9.200 / air outside south of dome in shado
#HIERARCH ESO TEL TSS TEMP10 END=      5.730 / plate sensor looking into sky top
#HIERARCH ESO TEL TSS TEMP10 START=    5.750 / plate sensor looking into sky top
#HIERARCH ESO TEL TSS TEMP11 END=     10.040 / air inside dome midheight
#HIERARCH ESO TEL TSS TEMP11 START=   10.090 / air inside dome midheight
#HIERARCH ESO TEL TSS TEMP12 END=     10.020 / air for instrument
#HIERARCH ESO TEL TSS TEMP12 START=    9.800 / air for instrument
#HIERARCH ESO TEL TSS TEMP13 END=     15.650 / surface delta hydrostatic pad
#HIERARCH ESO TEL TSS TEMP13 START=   15.630 / surface delta hydrostatic pad
#HIERARCH ESO TEL TSS TEMP14 END=      9.780 / air inside adapter
#HIERARCH ESO TEL TSS TEMP14 START=    9.710 / air inside adapter
#HIERARCH ESO TEL TSS TEMP2 END=      65.130 / air outside north of dome, road he
#HIERARCH ESO TEL TSS TEMP2 START=    65.260 / air outside north of dome, road he
#HIERARCH ESO TEL TSS TEMP3 END=      10.400 / air at low level in dome near floo
#HIERARCH ESO TEL TSS TEMP3 START=    10.380 / air at low level in dome near floo
#HIERARCH ESO TEL TSS TEMP4 END=       9.840 / surface of M1
#HIERARCH ESO TEL TSS TEMP4 START=     9.890 / surface of M1
#HIERARCH ESO TEL TSS TEMP5 END=      10.680 / air close to M1 surface
#HIERARCH ESO TEL TSS TEMP5 START=    10.680 / air close to M1 surface
#HIERARCH ESO TEL TSS TEMP6 END=       9.050 / surface midheight of lower Serruri
#HIERARCH ESO TEL TSS TEMP6 START=     9.050 / surface midheight of lower Serruri
#HIERARCH ESO TEL TSS TEMP7 END=      11.610 / surface midheight of upper Serruri
#HIERARCH ESO TEL TSS TEMP7 START=    11.630 / surface midheight of upper Serruri
#HIERARCH ESO TEL TSS TEMP8 END=      10.030 / surface on M2
#HIERARCH ESO TEL TSS TEMP8 START=    10.060 / surface on M2
#HIERARCH ESO TEL TSS TEMP9 END=       8.950 / air close to top ring
#HIERARCH ESO TEL TSS TEMP9 START=     8.920 / air close to top ring
#HIERARCH ESO TPL DID         = 'ESO-VLT-DIC.TPL-1.9' / Data dictionary for TPL
#HIERARCH ESO TPL EXPNO       =            2 / Exposure number within template
#HIERARCH ESO TPL ID          = 'GROND_img_obs_exp' / Template signature ID
#HIERARCH ESO TPL NAME        = 'Science Imaging' / Template name
#HIERARCH ESO TPL NEXP        =            1 / Number of exposures within templat
#HIERARCH ESO TPL PRESEQ      = 'GROND_img_obs_exp.seq' / Sequencer script
#HIERARCH ESO TPL START       = '2011-10-18T00:06:26' / TPL start time
#HIERARCH ESO TPL VERSION     = '$Revision: 1.4 $' / Version of the template
#H_CD1_1 =             0.000168          / WCS rotation matrix.
#H_CD1_2 =             0.000000          / WCS rotation matrix.
#H_CD2_1 =             0.000000          / WCS rotation matrix.
#H_CD2_2 =             0.000168          / WCS rotation matrix.
#H_CRPIX1=           512.000000          / WCS reference pixel X.
#H_CRPIX2=           512.000000          / WCS reference pixel Y.
#H_GAIN  =             2.650000          / H-band gain.
#H_RON   =            10.710000          / H-band Readout Noise.
#IMAGETYP= 'object  '                    / IRAF image type.
#J_CD1_1 =             0.000168          / WCS rotation matrix.
#J_CD1_2 =             0.000000          / WCS rotation matrix.
#J_CD2_1 =             0.000000          / WCS rotation matrix.
#J_CD2_2 =             0.000168          / WCS rotation matrix.
#J_CRPIX1=           512.000000          / WCS reference pixel X.
#J_CRPIX2=           512.000000          / WCS reference pixel Y.
#J_GAIN  =             2.390000          / J-band gain.
#J_RON   =             8.840000          / J-band Readout Noise.
#K_CD1_1 =             0.000168          / WCS rotation matrix.
#K_CD1_2 =             0.000000          / WCS rotation matrix.
#K_CD2_1 =             0.000000          / WCS rotation matrix.
#K_CD2_2 =             0.000168          / WCS rotation matrix.
#K_CRPIX1=           512.000000          / WCS reference pixel X.
#K_CRPIX2=           512.000000          / WCS reference pixel Y.
#K_GAIN  =             2.550000          / K-band gain.
#K_RON   =            11.930000          / K-band Readout Noise.
#LONPOLE =           180.000000          / Coordinate unit.
#NEWPOS  =                    T          / Preset the telescope?.
#NGR     =                    1          / Number of GR frames per telescope pos.
#NINT    =                    1          / No. of IR frames per mirror position.
#NIZ     =                    1          / Number of IZ frames per telescope pos.
#NMD     =                    6          / No. of mirror positions.
#NMP     =                    6          / No. of mirror movements per telpointin
#NTD     =                    4          / Number of telescope dither positions.
#NTP     =                    4          / Number of telescope movements per OB.
#OBSEQNUM=                    1          / Sequence number.
#OBSRUNID=                    1          / Observingrun number.
#OBTYPEID= '4m4td   '                    / OB type.
#RA2000  =           289.240218 / Telescope pointing.
#RADESYS = 'FK5     '                    / Coordinate unit.
#TARGETID= 'VB10    '                    / Target ID.
#TYPE    = 'science '                    / Exposure type.
#ARCFILE = 'GROND.2011-10-18T00:06:43.810.fits' / Archive File Name
#WCSDIM  =                    2 / # of wcs dimensions in frame.
#CD1_1   =  -8.4158764862796E-5 / WCS rotation matrix.
#CD2_2   =  8.41587648627960E-5 / WCS rotation matrix.
#LTM1_1  =                   1.
#LTM2_2  =                   1.
#WAT0_001= 'system=image'
#WAT1_001= 'wtype=tan axtype=ra'
#WAT2_001= 'wtype=tan axtype=dec'
#CRPIX1  =     919.950185054203 / WCS reference pixel X.
#CRPIX2  =      941.04112237867 / WCS reference pixel Y.
#FILTER  = 'J       '           / GROND Filter
#RON     =                 8.84 / Read out noise e-.
#GAIN    =                 2.39 / Gain e-/ADU.
#ZEROCOR = 'Nov 29 14:54 Zero level correction image is /diskc/home/fknust/data_'
#FLATCOR = 'Nov 29 14:54 Flat field image is /diskc/home/fknust/data_local/calib'
#CCDSEC  = '[1:1024,1:1024]'
#CCDPROC = 'Nov 29 14:54 CCD processing done'
#FIXPIX  = 'Nov 29 14:54 Bad pixel file is /diskc/home/fknust/data_red/VB10_move'
#MJD-MID =    55852.00667645907 / Midtime of OB in MJD.
#OBSERR  =    173.0357919819653 / Error of OB in s: (Tend-Tstart)/2.
#NCOMBINE=                   24
#TDP-MID =    55852.00486824907 / Midtime of TDP in MJD.
#TDPERR  =    16.80644801817834 / Error of TDP in s: (Tend-Tstart)/2.
#NIMGS   =                   24 / Total # of images.
#CD1_2   =  1.24928318144122E-6
#CD2_1   =  1.24928318144122E-6
#IMCORSTR= '1       '           / Image correction strategy
#INTERPSM=              1.77834 / Interpolation smoothing noise correction
#SKYMED  =      -0.202248845361
#OBJMASK = '/diskc/home/fknust/data_red/VB10_movement/VB10/OB1_1/J/GROND_J_OB_ms'
#SKYSUB  = 'Object masked and sky subtracted with nmean=3 nreject=1'
#AIRMASS =                1.387 / Average airmass of image.
#MOONDIST=          146.5108575 / Average moon distance to target.
#IMCMB001= 'GROND_J_TDP1_cor.fits'
#IMCMB002= 'GROND_J_TDP2_cor.fits'
#IMCMB003= 'GROND_J_TDP3_cor.fits'
#IMCMB004= 'GROND_J_TDP4_cor.fits'
#IMGEXP  =                 48.0 / Total exposure of image.
#ASTOK   =                    1 / Astrometry successful flag
