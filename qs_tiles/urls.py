from django.conf.urls.defaults import *
from qs_tiles import views

urlpatterns = patterns('',
    (r'^qs_tiles%s' % views.tile_request_pat, views.get_tile),
)
    
