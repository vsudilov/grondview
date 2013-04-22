class CoordinateParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse coordinates"
class AreaParseError(Exception):
  def __init__(self):
    self.msg = "Unable to parse area"
class NoCoverageError(Exception):
  def __init__(self,radius,units='arcseconds'):
    self.msg = "No GROND objects within %0.1f %s of given coordinates" % (radius,units)

