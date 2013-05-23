from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import login
from userena.views import signup
from grondview import settings

import grondview.views
import imagequery.views
import objectquery.views
import forcedetect.views
import accounts.views


from imagequery.forms import ImageQueryForm
from objectquery.forms import ObjectQueryForm

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', grondview.views.HomeView.as_view() ),
    url(r'^accounts/', include('userena.urls')),
    url(r'^accounts/(?P<user>[\w-]+)/sources/$',accounts.views.SourcesView.as_view() ),
    url(r'^accounts/(?P<user>[\w-]+)/delete/$',accounts.views.Authentication.as_view(method='delete') ),
    url(r'^logout/$', accounts.views.Authentication.as_view(method='logout')),
    url(r'^signup/$', signup ),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^(?P<page_name>contact|impressum|readme)/$', grondview.views.StaticView.as_view() ),
    url(r'^imagequery/$', grondview.views.FormView.as_view(form_class=ImageQueryForm) ),
    url(r'^objectquery/$', grondview.views.FormView.as_view(form_class=ObjectQueryForm) ),
    url(r'^sources/get_cutouts/$',imagequery.views.GetCutouts.as_view() ),
    url(r'^sources/(?P<sourceID>[\w:\.+-]+)/$',objectquery.views.ObjectView.as_view() ),
    url(r'^sources/(?P<user>[\w-]+)/(?P<sourceID>[\w:\.+-]+)/$',objectquery.views.ObjectView.as_view() ),
    url(r'^forcedetect/$',forcedetect.views.ForceDetectView.as_view() ),
    url(r'^forcedetect/(?P<jobid>[\w-]+)$', forcedetect.views.ForceDetectView.as_view() ),
    url(r'^fields/(?P<targetID>[\w:\.+-]+)/(?P<OB>\w+)/$',imagequery.views.FieldView.as_view() ),
    url(r'^fields/(?P<targetID>[\w:\.+-]+)/$',imagequery.views.FieldView.as_view() ),

    url(r'^download/(?P<TARGETID>[\w:\.+-]+)/(?P<OB>[\w:\.+-]+)$', grondview.views.DownloadImages.as_view() ),
    url(r'^download/(?P<TARGETID>[\w:\.+-]+)/$', grondview.views.DownloadImages.as_view() ),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
