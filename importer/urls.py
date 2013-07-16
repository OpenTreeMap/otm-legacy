from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('importer.views',
    (r'^$', 'list_imports'),
    (r'^create$', 'create'),
    (r'^status/tree/(?P<import_event_id>\d+)$', 'show_tree_import_status'),
    (r'^status/species/(?P<import_event_id>\d+)$', 'show_species_import_status'),
    (r'^update/(?P<import_event_row_id>\d+)$', 'update_row'),

    (r'^export/species/all', 'export_all_species'),
    (r'^export/species/(?P<import_event_id>\d+)$', 'export_single_species_import'),
    (r'^export/tree/(?P<import_event_id>\d+)$', 'export_single_tree_import'),

    # API
    (r'^api/(?P<import_type>[a-z]+)/(?P<import_event_id>\d+)/results/(?P<subtype>[a-zA-Z]+)$',
     'results'),
    (r'^api/(?P<import_type>[a-z]+)/(?P<import_event_id>\d+)/commit$', 'commit'),
    (r'^api/(?P<import_type>[a-z]+)/(?P<import_event_id>\d+)/update$', 'update'),
    (r'^api/species/(?P<import_event_id>\d+)/(?P<import_row_idx>\d+)/solve$', 'solve'),
    (r'^api/counts', 'counts'),
    (r'^api/species/similar', 'find_similar_species'),
)
