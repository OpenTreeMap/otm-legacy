from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin as FlatPageAdminOld
from django.contrib.gis import admin

editor = admin.AdminSite()

class FlatPageAdmin(FlatPageAdminOld):
    pass
    #class Media:
    #    js = ('/static/tiny_mce/tiny_mce.js',
    #          '/static/tiny_mce/textareas.js',)

# We have to unregister it, and then reregister
admin.site.unregister(FlatPage)
editor.register(FlatPage, FlatPageAdmin)