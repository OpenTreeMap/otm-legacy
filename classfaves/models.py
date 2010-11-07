import datetime

from django.db import models

from django.contrib.auth.models import User

class FavoriteBase(models.Model):
    """
    This is the abstract base class that you will subclass to create your own
    domain-specific Favorite model.
    """
    user = models.ForeignKey(User)
    
    date_created = models.DateTimeField(default=datetime.datetime.now)
    
    class Meta(object):
        abstract = True