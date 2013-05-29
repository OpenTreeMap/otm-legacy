from django.conf import settings
from django.contrib.gis.db import models

from treemap.models import Species

class TreeRegionPolygon(models.Model):
    region_id = models.FloatField()
    geometry = models.PolygonField(srid=4326)

class DBHClass(models.Model):
    label = models.CharField(max_length=255)
    dbh_min = models.FloatField()
    dbh_max = models.FloatField()

class TreeRegionEntry(models.Model):
    polygon = models.ForeignKey(TreeRegionPolygon)
    species = models.ForeignKey(Species)
    dbhclass = models.ForeignKey(DBHClass)
    count = models.IntegerField()
