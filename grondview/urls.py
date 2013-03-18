from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from grondview import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="home.html")),
    url(r'^login/$', 'grondview.views.login'),
    url(r'^logout/$', 'grondview.views.logout'), 

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^(?P<page_name>contact|impressum|readme)/$', 'grondview.views.staticpage'),
    url(r'^imagequery/$', 'imagequery.views.home'),
    url(r'^objectquery/$', 'objectquery.views.home'),
    url(r'^sources/(?P<sourceID>.*)$','objectquery.views.view_source'),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
