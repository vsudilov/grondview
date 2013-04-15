convert_arcmin_or_arcsec_to_degrees = {'arcminutes':1/60.,'arcseconds':1/3600.,'degrees':1}

GrondFilters = {
  'g': {'lambda_eff': 458.69},
  'r': {'lambda_eff': 621.98},
  'i': {'lambda_eff': 764.07},
  'z': {'lambda_eff': 898.96},
  'J': {'lambda_eff': 1239.92},
  'H': {'lambda_eff': 1646.84},
  'K': {'lambda_eff': 2170.55},
  }

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

obtypes = ['30m6td','20m4td','10m6td','8m4td','4m4td']
obtypes_sequence = dict([(o,obtypes.index(o)+1) for o in obtypes])
