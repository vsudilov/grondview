from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.core.exceptions import PermissionDenied

from objectquery.models import AstroSource, Photometry
from forcedetect.views import JSONResponseMixin
from accounts.models import UserProfile, UserSourceNames

import json

class NameView(JSONResponseMixin,View):
  def post(self,request,*args,**kwargs):
    s = AstroSource.objects.filter(sourceID=request.POST['sourceID'])[0]
    try:
      usn = UserSourceNames.objects.get(user=request.user,astrosource=s)
      usn.name = request.POST['name']
      usn.save()
    except UserSourceNames.DoesNotExist:
      fields = {}
      fields['user'] = request.user
      fields['astrosource'] = s
      fields['name'] = request.POST['name']
      usn = UserSourceNames(**fields)
      usn.save()
    context = {'completed':True,'name':UserSourceNames.objects.get(user=request.user,astrosource=s).name}
    return self.render_to_response(context)

class TagView(JSONResponseMixin,View):
  def post(self,request,*args,**kwargs):
    profile = UserProfile.objects.get(user=request.user)
    s = AstroSource.objects.filter(sourceID=request.POST['sourceID'])[0]
    if s not in profile.tagged_sources.all():
      profile.tagged_sources.add(s)
    else:
      profile.tagged_sources.remove(s)
    profile.save()
    context = {'completed':True}
    return self.render_to_response(context)

class SourcesView(JSONResponseMixin,TemplateView):
  template_name = 'content/usersources_content.html'
  def get(self, request, *args, **kwargs):
    if kwargs['user'] != request.user.username:
      raise PermissionDenied

    #User sources
    results = AstroSource.objects.filter(user=request.user)
    data = {}

    for i in results:
      _id = i.sourceID
      data[_id] = {}
      data[_id]['n_detections'] = Photometry.objects.filter(astrosource__sourceID=i.sourceID).count()
      data[_id]['RA'] = i.RA
      data[_id]['DEC'] = i.DEC
      try:
        data[_id]['name'] = UserSourceNames.objects.get(user=request.user,astrosource=i)
      except UserSourceNames.DoesNotExist:
        data[_id]['name'] = None

    #Force detected sources
    results = Photometry.objects.filter(user=request.user).distinct('astrosource__sourceID')
    pdata = {}
    for i in results:
      _id = i.astrosource.sourceID
      pdata[_id] = {}
      pdata[_id]['n_detections'] = Photometry.objects.filter(astrosource__sourceID=_id).filter(user=request.user).count()
      try:
        pdata[_id]['name'] = UserSourceNames.objects.get(user=request.user,astrosource=i)
      except UserSourceNames.DoesNotExist:
        pdata[_id]['name'] = None
      pdata[_id]['ownership'] = i.astrosource.user.username

    #Tagged sources
    tdata = {}
    profile = UserProfile.objects.get(user=request.user)
    for i in profile.tagged_sources.all():
      _id = i.sourceID
      tdata[_id] = {}
      tdata[_id]['RA'] = i.RA
      tdata[_id]['DEC'] = i.DEC
      tdata[_id]['ownership'] = i.user.username
      try:
        tdata[_id]['name'] = UserSourceNames.objects.get(user=request.user,astrosource=i).name
      except UserSourceNames.DoesNotExist:
        tdata[_id]['name'] = None
    context = {'user_sources_data':json.dumps(data),
               'user_photometry_data':json.dumps(pdata),
               'user_tagged_sources':json.dumps(tdata)}
    return render(request,self.template_name,context)

  def post(self, request, *args, **kwargs):
    if kwargs['user'] != request.user.username:
      raise PermissionDenied
    try:
      model = request.POST['model']
      sourceID = request.POST['sourceID']
    except:
      return HttpResponseBadRequest()
    
    if model=="astrosource":
      result = AstroSource.objects.filter(sourceID=sourceID).get(user=request.user)
      result.delete()
    if model=="photometry":
      results = Photometry.objects.filter(astrosource__sourceID=sourceID).filter(user=request.user)
      [i.delete() for i in results]
    context = {'completed':True}
    return self.render_to_response(context)

class Authentication(TemplateView):
  template_name = 'userena/confirm_delete.html'
  method = None #Set in urls.py

  def get(self, request, *args, **kwargs):
    return render(request,self.template_name)

  def post(self, request, *args, **kwargs):
    try:
      pwd1 = request.POST['pwd1']
      pwd2 = request.POST['pwd2']
      assert pwd1==pwd2
    except:
      context = {'errors': 'Bad input. Try again'}
      return render(request,self.template_name,context)
    if not request.user.check_password(pwd1):
      raise PermissionDenied
    [i.delete() for i in AstroSource.objects.filter(user=request.user)]
    [i.delete() for i in Photometry.objects.filter(user=request.user)]
    cu = User.objects.get(username=request.user.username)
    cu.delete()
    auth.logout(request)
    return HttpResponseRedirect('/')
    
  def dispatch(self, request, *args, **kwargs):
    if self.method == 'logout':
      auth.logout(request)
      return HttpResponseRedirect('/')
    return super(Authentication, self).dispatch(request, *args, **kwargs)        

