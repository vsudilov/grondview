from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.template import RequestContext
from django.template import TemplateDoesNotExist
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils.importlib import import_module

from grondview.forms import LoginForm



#---------------------------------------------------------------
class GenericDataContainer(object):
  '''
  Defines a generic data container that is expanded in templates.
  This class is responsible for sorting and grouping results from
  executed QuerySets.

  Example usage in views.py:

  GenericDataContainer(name="target1")
  d = {'BAND':'r','MAG_PSF':1}
  data.appendOB("OB3_1",d)
  d = {'BAND':'J','MAG_PSF':2}
  data.appendOB("OB3_1",d)
  d = {'BAND':'H','MAG_PSF':3}
  data.appendOB("OB3_1",d)
  d = {'BAND':'i','MAG_PSF':4}
  data.appendOB("OB3_1",d)
  d = {'BAND':'z','MAG_PSF':1.1}
  data.appendOB("OB3_2",d)
  d = {'BAND':'J','MAG_PSF':1.2}
  data.appendOB("OB3_2",d)
  d = {'BAND':'K','MAG_PSF':1.3}
  data.appendOB("OB3_2",d)
  d = {'BAND':'i','MAG_PSF':1.4}
  data.appendOB("OB3_2",d)
  d = {'BAND':'g','MAG_PSF':1.11}
  data.appendOB("OB1_5",d)
  d = {'BAND':'r','MAG_PSF':1.22}
  data.appendOB("OB1_5",d)
  d = {'BAND':'i','MAG_PSF':1.33}
  data.appendOB("OB1_5",d)
  d = {'BAND':'z','MAG_PSF':1.44}
  data.appendOB("OB1_5",d)

  data.sortOBs()
  data.sortBands()

  Example usage in template:
  
  <h1>SourceID: {{data.name}}</h1>
  <p> Distance from input coordinates: {{data.distance}} </p>
  <p> Another useful attribute: {{data.usefulAttribute}} </p>
  {% for OB in data.OBs %}
    <h2>OB: {{OB.OBname}}</h2>
    <p>OB Type: {{OB.type}}</h2>
    {% for d in OB %}
    <ul>
    <li>d.BAND</li>
    <li>d.MAG_PSF</li>
    <li>d.yetAnotherUsefulAttr</li>
    </ul 
  
  The keys/values of the innermost dict (`d`) are completely arbitrary, 
  thus enabling flexibility in how this class is used.
  '''

  def __init__(self,name,**kwargs):
    self.name = name
    self.OBs = []
    for k in kwargs:
        self.__setattr__(k,kwargs[k])
  
  def appendOB(self,OBname,data,**kwargs):
    OBnames = [OB.OBname for OB in self.OBs]
    if OBname not in OBnames:
      self.OBs.append(self._OBContainer(OBname=OBname,**kwargs))
    [OBContainer.data.append(data) for OBContainer in self.OBs if OBContainer.OBname==OBname]
        

  def sortOBs(self):
    def _sortListByOB(L):
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

      return sorted(L,key=lambda k: keyfunc(k.OBname))
    
    self.OBs = _sortListByOB(self.OBs)


  def sortBands(self):
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

    for OB in self.OBs:
      OB.data = sortListDictByBand(OB.data)


  class _OBContainer(object):
    def __init__(self,OBname,**kwargs):
      self.data = []
      self.OBname = OBname
      for k in kwargs:
        self.__setattr__(k,kwargs[k])



def login(request):
  if request.method == 'POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      username = request.POST['username']
      passwd = request.POST['passwd']
      user = auth.authenticate(username=username, password=passwd)
      if user is not None:
        if user.is_active:
          auth.login(request, user)
          # Redirect to a success page.
        return HttpResponseRedirect('/')
    return render(request,'login.html',{'form': form, 'invalid_login':True})
  else:
    form = LoginForm()
    return render(request,'login.html',{'form': form})
#---------------------------------------------------------------





def logout(request):
  auth.logout(request)
  return HttpResponseRedirect('/')

def staticpage(request, page_name):
    # Use some exception handling, just to be safe
    try:
        return direct_to_template(request, '%s.html' % (page_name, ))
    except TemplateDoesNotExist:
        raise Http404

