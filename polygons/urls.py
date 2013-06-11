from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    (r'^search/$', polygon_search),
    (r'^[0-9]+/$', polygon_view),
)
