from django import template

register = template.Library()

@register.filter
def sortListDictByBand(L,band_kw='BAND'):
  '''
  Sorts a list of dicts by their band, ie
  L = [{'BAND':'r'},{'BAND':'g'},{'BAND':'H'}}
  {{ L|sortListDictByBand }}
    --> [{'BAND':'g'},{'BAND':'r'},{'BAND':'H'}]
  '''
  pattern = {} #-- Order that the bands should be sorted
  pattern['g'] = 1
  pattern['r'] = 2
  pattern['i'] = 3
  pattern['z'] = 4
  pattern['J'] = 5
  pattern['H'] = 6
  pattern['K'] = 7
  return sorted(L,key=lambda k: pattern[k[band_kw]])

@register.filter
def sortListByOB(L):
  '''
  Sorts a list by their OB, ie
  L = ['OB1_2','OB1_1','OB1_5']
  {{ L|sortListByBand }}
    --> ['OB1_1','OB1_2','OB1_5']
  '''
  import re
  def keyfunc(s):
    s = re.search('\d+_\d+',s).group()
    return map(int,s.split('_'))
  return sorted(L,key=lambda k: keyfunc(k))
