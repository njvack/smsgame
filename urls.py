from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from sampler import urls as sampler_urls

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'smsgame.views.home', name='home'),
    # url(r'^smsgame/', include('smsgame.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url('', include(sampler_urls.urlpatterns)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root' : settings.PUBLIC_DIR})
    )