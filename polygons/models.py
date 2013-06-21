from django.conf import settings
from django.contrib.gis.db import models

from treemap.models import Species, User
from treemap import audit

class TreeRegionPolygon(models.Model):
    region_id = models.FloatField()
    geometry = models.PolygonField(srid=4326)

    photo = models.ImageField(upload_to="polygons/%Y/%m/%d",null=True,blank=True)
    objects = models.GeoManager()

    # required for audit trail
    history = audit.AuditTrail()
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User,
                                        related_name='treeregionpolygon_updated_by')

    def __unicode__(self):
        return u"Polygon #%s, Region ID: %s" % (self.pk, self.region_id)

class DBHClass(models.Model):
    label = models.CharField(max_length=255)
    dbh_min = models.FloatField()
    dbh_max = models.FloatField()

    def __unicode__(self):
        return u"DBH Class #%s: %s (%s - %s)" % \
            (self.pk, self.label, self.dbh_min, self.dbh_max)

class TreeRegionEntry(models.Model):
    polygon = models.ForeignKey(TreeRegionPolygon)
    species = models.ForeignKey(Species)
    dbhclass = models.ForeignKey(DBHClass)
    count = models.IntegerField(default=0)

    objects = models.GeoManager()

    # required for audit trail
    history = audit.AuditTrail()
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User,
                                        related_name='treeregionentry_updated_by')

    def __unicode__(self):
        return u"%s, Species: %s, Count: %s" % \
            (str(self.polygon), str(self.species), self.count)
