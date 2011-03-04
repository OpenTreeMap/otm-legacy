import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Count, Sum
from UrbanForestMap.treemap import models 


class Command(BaseCommand):
   
    def handle(self, *args, **options):
        for t in Trees.objects.all():
            if t.current_dbh:
                t.save()

