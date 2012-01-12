import datetime
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Count, Sum, Q
from OpenTreeMap.treemap import models 


class Command(BaseCommand):
   
    def handle(self, *args, **options):
        self.update_all_aggregates()


    def update_aggregates(self, base_model, ag_model):
        """
        Updates the aggregate tables.  TODO:  don't just overwrite old summaries
        example: update_aggregates(Neighborhood, AggregateNeighborhood)
        """
        start_time = time.time()
        ns = base_model.objects.all()
        field_names = [x.name for x in models.ResourceSummaryModel._meta.fields 
            if not x.name == 'id']
        for n in ns:
            print n
            agg =  ag_model.objects.filter(location=n)
            if agg:
                agg = agg[0]
            else:
                agg = ag_model(location=n)
            trees = models.Tree.objects.filter(plot__geometry__within=n.geometry)
            plots = models.Plot.objects.filter(geometry__within=n.geometry)
            agg.total_trees = trees.count()
            agg.total_plots = plots.count()
            #agg.distinct_species = len(trees.values("species").annotate(Count("id")).order_by("species"))
            #TODO figure out how to summarize diff stratum stuff
            trees = trees.exclude( Q(dbh=None) | Q(dbh=0.0) ).exclude(species=None)
            for f in field_names:
                if agg.total_trees == 0:
                    s = 0.0
                else:
                    fn = 'treeresource__' + f   
                    s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                print agg,f,s
                setattr(agg,f,s)
            agg.save()
        end_time = time.time()
        print "done in ", float(end_time) - float(start_time), "seconds"

    def cache_search_aggs(self, query_pairs=({'trees':models.Tree.objects.all(),'query':''},),return_first=False):
        #fields = ['annual_stormwater_management', 'annual_electricity_conserved', 
        #          'annual_natural_gas_conserved', 'annual_air_quality_improvement', 
        #          'annual_co2_sequestered', 'total_co2_stored', 
        #          'annual_co2_avoided'
        #          ]
                  #'total_trees', 'distinct_species'
        for q in query_pairs:
            agg = models.AggregateSearchResult.objects.filter(key=q['query'])
            if agg:
                agg = agg[0]
            else:
                agg = models.AggregateSearchResult(key=q['query'])
            #if not new:
            #    agg.key = 
            trees = q['trees']
            # call len seems to cause deep crashing in python threads...
            #agg.total_trees = len(trees)
            #agg.distinct_species = len(trees.values("species").annotate(Count("id")).order_by("species"))
            agg.total_trees = trees.count()
            #agg.distinct_species = trees.values("species").annotate(Count("id")).order_by("species").count()

            #TODO figure out how to summarize diff stratum stuff
            fields = [x.name for x in models.ResourceSummaryModel._meta.fields 
                if not x.name in ['id','aggregatesummarymodel_ptr','key','resourcesummarymodel_ptr','last_updated']]
            for f in fields:
                    fn = 'treeresource__' + f
                    s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                    print agg,f,s
                    setattr(agg,f,s)
            agg.save()
            print 'saving', agg
            if return_first:
                return agg


    def update_all_aggregates(self, verbose=False):
        #if not tree_geom: return
        self.update_aggregates(models.Neighborhood, models.AggregateNeighborhood)
        self.update_aggregates(models.ZipCode, models.AggregateZipCode)
        #cache_search_aggs()
