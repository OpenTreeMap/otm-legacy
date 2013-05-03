from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('importer.views',
    (r'^$', 'index'),
)
