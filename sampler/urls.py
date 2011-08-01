from django.conf.urls.defaults import *
import views

urlpatterns = patterns(''
    ,(r'^tropo$', views.tropo)
    ,(r'^incoming$', views.incoming_message)
    ,(r'^request_baseline', views.request_baseline)
)