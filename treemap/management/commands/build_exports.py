import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from UrbanForestMap import settings
from UrbanForestMap.treemap import models
from UrbanForestMap.treemap.spreadsheet import queryset_to_excel_file 
from django.template import loader
from django.contrib.gis.shortcuts import compress_kml

class Command(BaseCommand):
   
    def handle(self, *args, **options):
        print "Getting all trees..."
        trees = models.Tree.objects.filter(present=True)
        print "Writing %i trees to CSV" % trees.count()
        queryset_to_excel_file(trees, "All_Trees",force_csv=True)
        print "Getting kml strings..."        
        trees = trees.kml()
        output = file('All_Trees.kmz','wb')
        print "Writing %i trees to KML" % trees.count()
        output.write(compress_kml(loader.render_to_string("treemap/kml_output.kml", {'trees': trees,'root_url':settings.ROOT_URL})))
        output.close()




    def write_csv(self, trees):
        clip_length = 5000
        current_clip = 5000
        tree_clip = trees[:current_clip]
        output = file('All_Trees.csv','ab')
        output.truncate(0)
        while tree_clip:
            data = list(tree_clip.values())
            for row in data:
                out_row = []
                for value in row:
                    if not isinstance(value, basestring):
                        value = unicode(value)
                    value = value.encode(encoding)
                    out_row.append(value.replace('"', '""'))
                output.write('"%s"\n' %
                             '","'.join(out_row))
            tree_clip = trees[current_clip+1:current_clip + clip_length]
            current_clip = current_clip + clip_length
        output.close()
