from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('importer.views',
    (r'^start$', 'start'),
    (r'^list$', 'list_imports'),
    (r'^create$', 'create'),
    (r'^status/(?P<import_event_id>\d+)$', 'show_import_status'),
    (r'^update/(?P<import_event_row_id>\d+)$', 'update_row'),

    # API
    (r'^api/(?P<import_event_id>\d+)/results/(?P<subtype>[a-zA-Z]+)$', 'results'),
    (r'^api/(?P<import_event_id>\d+)/commit$', 'commit'),
)
