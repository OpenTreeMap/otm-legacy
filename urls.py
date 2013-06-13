from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib import databrowse

from django.contrib import admin
admin.autodiscover()


from registration.views import register

urlpatterns = patterns('',
    (r'^_admin_/', include(admin.site.urls)),
    (r'^databrowse/(.*)', databrowse.site.root),

    (r'^static/css/images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DATA + "/images/" + settings.SITE_LOCATION}),

    (r'^static/css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DATA + "/css/" + settings.SITE_LOCATION}),
    (r'^static/images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DATA + "/images/" + settings.SITE_LOCATION}),
    #(r'^static/js/(?P<path>.*)$', 'django.views.static.serve',
    #    {'document_root': settings.STATIC_DATA + "/js/" + settings.SITE_LOCATION}),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DATA}),
    (r'^Species/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT + "/Species"}),
    (r'^Nodes/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT + "/Nodes"}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
    (r'^admin_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.ADMIN_MEDIA_ROOT}),
    (r'^comments/', include('threadedcomments.urls')),

    (r'^', include('treemap.urls')),
    (r'^importer/', include('importer.urls')),
    #(r'^', include('qs_tiles.urls')),

    # using new 0.8 beta with "backends" support
    # http://docs.b-list.org/django-registration/0.8/
    # override just the /register view to customize form and save actions...
    url(r'^accounts/register/$',register,
       { 'backend': 'registration_backend.TreeBackend' },
       name='registration_register'),
    # dispatch the remainder of the urls to the default backend...
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^profiles/', include('profiles.urls')),
    (r'^treekey/', include('treekey.urls')),
    (r'^api/v0.1/', include('api.urls')),
)

if 'polygons' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^polygons/', include('polygons.urls')),
    )
