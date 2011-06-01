import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Count, Sum
from UrbanForestMap.treemap.models import Tree


class Command(BaseCommand):
   
    def handle(self, *args, **options):
        for t in Tree.objects.all():
            if t.dbh:
                print t.id
                t.save()

