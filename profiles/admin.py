from django.contrib.gis import admin
from django.contrib.gis.admin.options import OSMGeoAdmin
from profiles.models import *

class UserProfileAdmin(OSMGeoAdmin):
    actions_on_top = False
    #list_display = ('user', 'full_name','email','account_activated','remove',)
    #list_filter = (' ',)

admin.site.register(UserProfile, UserProfileAdmin)
