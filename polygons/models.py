from django.conf import settings
from django.contrib.gis.db import models

from treemap.models import Species

class TreeRegionPolygon(models.Model):
    region_id = models.FloatField()
    geometry = models.PolygonField(srid=4326)

    photo = models.ImageField(upload_to="polygons/%Y/%m/%d",null=True,blank=True)
    objects = models.GeoManager()

class DBHClass(models.Model):
    label = models.CharField(max_length=255)
    dbh_min = models.FloatField()
    dbh_max = models.FloatField()

class TreeRegionEntry(models.Model):
    polygon = models.ForeignKey(TreeRegionPolygon)
    species = models.ForeignKey(Species)
    dbhclass = models.ForeignKey(DBHClass)
    count = models.IntegerField(default=0)

    objects = models.GeoManager()
