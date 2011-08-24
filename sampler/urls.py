from django.conf.urls.defaults import *

urlpatterns = patterns(''
    ,url(r'^tropo$', 'sampler.views.tropo')
    ,url(r'^experiments/(?P<slug>[A-Za-z0-9_]+)/experiencesamples.csv$',
        'sampler.views.experiencesamples_csv')
)
