from django.conf.urls.defaults import *

urlpatterns = patterns(''
    ,url(r'^tropo$', 'sampler.views.tropo')
)