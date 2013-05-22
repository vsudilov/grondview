from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect

class SourcesView(TemplateView):
  template_name = 'content.html'
  def get(self, request, *args, **kwargs):
    context = {}
    context['user_sources_data'] = 'abc'
    return render(request,self.template_name,context)


class Authentication(TemplateView):
  template_name = 'content.html'
  method = None #Set in urls.py

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST)
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
  def get(self, request, *args, **kwargs):
      return render(request,'login.html',{'form': self.form_class})

  def dispatch(self, request, *args, **kwargs):
    if self.method == 'logout':
      auth.logout(request)
      return HttpResponseRedirect('/')
    if self.method == 'delete':
      auth.logout(request)
      return HttpResponseRedirect('/')
    return super(Authentication, self).dispatch(request, *args, **kwargs)        

