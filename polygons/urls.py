from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    (r'^search/$', polygon_search),
    (r'^recent/$', recent_edits),
    (r'^(?P<polygon_id>[0-9]+)/$', polygon_view),
    (r'^(?P<polygon_id>[0-9]+)/edit$', polygon_edit),
    (r'^(?P<polygon_id>[0-9]+)/update$', polygon_update),
    (r'^(?P<polygon_id>[0-9]+)/photo$', polygon_update_photo),
)
