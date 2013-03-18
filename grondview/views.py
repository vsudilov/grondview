from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import auth
from django.template import RequestContext
from django.template import TemplateDoesNotExist
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils.importlib import import_module

from grondview.forms import LoginForm





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


def logout(request):
  auth.logout(request)
  return HttpResponseRedirect('/')

def staticpage(request, page_name):
    # Use some exception handling, just to be safe
    try:
        return direct_to_template(request, '%s.html' % (page_name, ))
    except TemplateDoesNotExist:
        raise Http404

