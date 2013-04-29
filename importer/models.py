from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User

from treemap.models import Plot

import json

class TreeImportEvent(models.Model):
    """
    A TreeImportEvent represents an attempt to upload a csv containing
    tree/plot information
    """

    # Original Name of the file
    file_name = models.CharField(max_length=255)

    # We can do some numeric conversions
    plot_length_conversion_factor = models.FloatField(default=1.0)
    plot_width_conversion_factor = models.FloatField(default=1.0)
    diameter_conversion_factor = models.FloatField(default=1.0)
    tree_height_conversion_factor = models.FloatField(default=1.0)
    canopy_height_conversion_factor = models.FloatField(default=1.0)

    # Global errors and notices (json)
    errors = models.TextField(default='')

    # Metadata about this particular import
    owner = models.ForeignKey(User)
    created = models.DateTimeField(auto_now=True)
    completed = models.DateTimeField(null=True,blank=True)

    def append_error(self, err, data=None):
        code, msg, fatal = err

        if self.errors is None or self.errors == '':
            self.errors = '[]'

        self.errors = json.dumps(
            json.loads(self.errors) + [
                {'code': code,
                 'msg': msg,
                 'data': data,
                 'fatal': fatal}])

        return self



class TreeImportRow(models.Model):
    """
    A row of data and import status
    """

    # JSON dictionary from header <-> rows
    data = models.TextField()

    finished = models.BooleanField(default=False)

    # JSON field containing error information
    errors = models.TextField(default='')

    # plot that was created from this row
    plot = models.ForeignKey(Plot, null=True, blank=True)

    # The main import event
    import_event = models.ForeignKey(TreeImportEvent)

    def __init__(self, *args, **kwargs):
        super(TreeImportRow, self).__init__(*args,**kwargs)
        self.jsondata = None

    @property
    def datadict(self):
        if self.jsondata is None:
            self.jsondata = json.loads(self.data)

        return self.jsondata

    def append_error(self, err, data=None):
        code, msg, fatal = err

        if self.errors is None or self.errors == '':
            self.errors = '[]'

        self.errors = json.dumps(
            json.loads(self.errors) + [
                {'code': code,
                 'msg': msg,
                 'data': data,
                 'fatal': fatal}])

        return self
