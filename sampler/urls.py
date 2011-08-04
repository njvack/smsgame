from django.conf.urls.defaults import *

urlpatterns = patterns(''
    ,url(r'^tropo$', 'sampler.views.tropo')
    ,url(r'^incoming$', 'sampler.views.incoming_message')
    ,url(r'^request_baseline', 'sampler.views.request_baseline')
)