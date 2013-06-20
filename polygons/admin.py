from django.contrib.gis import admin
from polygons.models import TreeRegionPolygon, DBHClass, TreeRegionEntry

admin.site.register(DBHClass)
admin.site.register(TreeRegionEntry)
