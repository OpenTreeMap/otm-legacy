from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('django.views.generic.simple',    
    ('^$', 'redirect_to', {'url': './start'}),
)


urlpatterns += patterns('treekey.views',
    (r'^node/(?P<node_id>\d+)/$', 'node'),
    (r'^leaf/(?P<node_id>\d+)/$', 'node'),
    (r'^start/$', 'first_node'),
    (r'^species/(?P<species_id>\d+)/$', 'species'),
    (r'^browse/$', 'browse'),
    
    (r'^admin/', include(admin.site.urls)),
)
