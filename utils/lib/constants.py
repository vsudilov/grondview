convert_arcmin_or_arcsec_to_degrees = {'arcminutes':1/60.,'arcseconds':1/3600.,'degrees':1}

grondfilters = {
  'g': {'lambda_eff': 458.69},
  'r': {'lambda_eff': 621.98},
  'i': {'lambda_eff': 764.07},
  'z': {'lambda_eff': 898.96},
  'J': {'lambda_eff': 1239.92},
  'H': {'lambda_eff': 1646.84},
  'K': {'lambda_eff': 2170.55},
  }

pixelscale = {'g':0.158,'r':0.158,'i':0.158,'z':0.158,'J':0.6/2,'H':0.6/2,'K':0.6/2}

gain_IR = {'J':2.39,'H':2.65,'K':2.55}

INTERPSM = {'g':1.07,'r':1.07,'i':1.07,'z':1.07,'J': 1.77834,'H': 1.77834,'K': 1.77834}

convert_to_AB = {
        'g': 0,
        'r': 0,
        'i': 0,
        'z': 0,
        'J': 0.929,
        'H': 1.394,
        'K': 1.859, 
        }

bands = 'grizJHK'
band_sequence =  dict([(b,bands.index(b)+1) for b in bands])
optical = 'griz'
infrared = 'JHK'

obtypes = ['30m6td','20m4td','12m6td','10m6td','8m4td','4m4td','2m2td','1m1td']
obtypes_sequence = dict([(o,obtypes.index(o)+1) for o in obtypes])

extinction_coefficients = {
    'U':0.45,
    'B':0.22, 
    'V':0.12,
    'R':0.09, 
    'I':0.05,
    'g':0.16, 
    'r':0.09, 
    'i':0.04, 
    'z':0.04,
    'Y': 0.08, 
    'J':0.12, 
    'H':0.06, 
    'K':0.07, 
    'NB1190':0.12}

def arclength(ra1,dec1,ra2,dec2):
  from math import cos, sin, acos, degrees, radians, pi
  if ra1==ra2 and dec1==dec2:
    return 0

  def cosd(degs):
    return cos(degs*pi/180)
  return (    (    (ra1-ra2)*cosd(  (dec1+dec2)/2.0  )  )**2 + (dec1-dec2)**2)**(1/2.)*60.*60.
