from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    (r'^search/$', polygon_search),
    (r'^(?P<polygon_id>[0-9]+)/$', polygon_view),
    (r'^(?P<polygon_id>[0-9]+)/edit$', polygon_edit),
    (r'^(?P<polygon_id>[0-9]+)/update$', polygon_update),
)
