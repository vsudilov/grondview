from django.conf.urls import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.contrib import admin
from grondview import settings

admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', direct_to_template, {'template':'home.html'}),
     url(r'^login/$', 'grondview.views.login'),
     url(r'^logout/$', 'grondview.views.logout'), 
    
     url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
     url(r'^admin/', include(admin.site.urls)),

     url(r'^(?P<page_name>contact|projects|CV)/$', 'grondview.views.staticpage'),
     url(r'^imagequery/$', 'imagequery.views.home'),
     url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
