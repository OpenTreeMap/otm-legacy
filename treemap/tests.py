import os

# Note that test_utils forces some settings to reasonable values
# and should be imported before any other django based things
from api.test_utils import setupTreemapEnv, teardownTreemapEnv, mkTree, mkPlot
from treemap.test_choices import *
from django.conf import settings

settings.CHOICES = CHOICES
settings.POSTAL_CODE_FIELD = "USZipCodeField"

from django import forms
from django.test import TestCase, TransactionTestCase
from django.db import connection

from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.contrib.auth.models import User, UserManager, Permission as P

from treemap.models import Neighborhood, ZipCode, ExclusionMask
from treemap.models import Plot, ImportEvent, Species, Tree, TreeFlags
from treemap.models import BenefitValues, Resource, AggregateNeighborhood
from treemap.views import *
from treemap.shortcuts import get_add_initial

from profiles.models import UserProfile
from django_reputation.models import Reputation, ReputationAction

from simplejson import loads
from datetime import timedelta, datetime, date
from time import mktime

from test_util import set_auto_now

from export import _sanitize_native_status_field, _sanitize_membership_test_field, sanitize_raw_sql

import django.shortcuts
import tempfile
import zipfile
import shutil

class EcoBenefitTests(TestCase):

    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")

        ExclusionMask.objects.all().delete()

    def tearDown(self):
        settings.MULTI_REGION_ITREE_ENABLED = False

    def _resource_as_dict(self, tr):
        things = ['annual_stormwater_management',
                  'annual_electricity_conserved',
                  'annual_energy_conserved',
                  'annual_natural_gas_conserved',
                  'annual_air_quality_improvement',
                  'annual_co2_sequestered',
                  'annual_co2_avoided',
                  'annual_co2_reduced',
                  'total_co2_stored',
                  'annual_ozone',
                  'annual_nox',
                  'annual_pm10',
                  'annual_sox',
                  'annual_voc',
                  'annual_bvoc']

        return {thing: getattr(tr, thing) for thing in things}

    def test_simple_eco_generation(self):
        species = Species.objects.get(symbol="s1")

        plot = mkPlot(self.u,)
        tree = mkTree(self.u, plot, species=species)
        tree.dbh = 23.0

        tree.save()

        tr = TreeResource.objects.get(tree=tree)

        for benefit_value in self._resource_as_dict(tr).values():
            self.assertTrue(benefit_value is not None and
                            benefit_value != 0.0)


    def test_location_based_itree_benefits(self):
        settings.MULTI_REGION_ITREE_ENABLED = True
        pt1 = Point(5,5)
        pt2 = Point(-5, -5)

        p1 = Polygon( ((0, 0), (10, 0), (10, 10), (0, 10), (0, 0)) )
        p2 = Polygon( ((0, 0), (-10, 0), (-10, -10), (0, -10), (0, 0)) )

        p1 = MultiPolygon(p1)
        p2 = MultiPolygon(p2)

        c1 = ClimateZone(geometry=p1, itree_region='CaNCCoJBK')
        c2 = ClimateZone(geometry=p2, itree_region='CenFlaXXX')

        c1.save()
        c2.save()

        rsrc1 = Resource(meta_species="BDM OTHER", region="CaNCCoJBK")
        rsrc2 = Resource(meta_species="BDM OTHER", region="CenFlaXXX")
        rsrc1.save()
        rsrc2.save()

        species = Species.objects.get(symbol="s1")
        species.resource = [rsrc1, rsrc2]
        species.save()

        plot = mkPlot(self.u)
        plot.geometry = pt1
        plot.save()

        self.assertEqual(plot.itree_region(), 'CaNCCoJBK')

        tree = mkTree(self.u, plot, species=species)
        tree.dbh = 23.0
        tree.save()

        tr1 = self._resource_as_dict(TreeResource.objects.get(tree=tree))

        plot.geometry = pt2
        plot.save()

        self.assertEqual(plot.itree_region(), 'CenFlaXXX')

        tree = Tree.objects.get(pk=tree.pk)

        tr2 = self._resource_as_dict(TreeResource.objects.get(tree=tree))

        self.assertNotEqual(tr1, tr2)



# Needs to be a TransactionTestCase because
# we use ogr2ogr externally for csv generation
class SpeciesViewTests(TransactionTestCase):

    #TODO: Remove what we don't need here...
    def setUp(self):
        setupTreemapEnv()

        self.z1 = ZipCode.objects.get(zip="19-107")
        self.n1 = Neighborhood.objects.get(name="n1")

        self.u = User.objects.get(username="jim")

        p1_no_tree = mkPlot(self.u,)
        p2_tree = mkPlot(self.u)
        p3_tree_species1 = mkPlot(self.u)
        p4_tree_species2 = mkPlot(self.u)

        self.s1 = Species.objects.get(symbol="s1")
        self.s2 = Species.objects.get(symbol="s2")
        self.s3 = Species.objects.get(symbol="s3")

        t1 = mkTree(self.u, p2_tree, species=None)
        t2 = mkTree(self.u, p3_tree_species1, self.s1)
        t3 = mkTree(self.u, p4_tree_species2, self.s2)

        self.p1_no_tree = p1_no_tree
        self.p2_tree = p2_tree
        self.p3_tree_species1 = p3_tree_species1;
        self.p4_tree_species2 = p4_tree_species2;

        self.plots = [p1_no_tree, p2_tree, p3_tree_species1, p4_tree_species2]

        self.t1 = t1
        self.t2 = t2
        self.t3 = t3

        self.ie = ImportEvent.objects.get(file_name='site_add')

    def test_full_species_list(self):
        """
        different ways to get the full list:
        - no args
        - all

        With and without 'json'
        """

        # With no additional params, we expect to render an
        # html page. That page should get a context object
        # of species
        response = self.client.get("/species/")
        self.assertTemplateUsed(response, 'treemap/species.html')

        context_ids = set([s.pk for s in response.context["species"]])
        db_ids = set([s.pk for s in Species.objects.all()])

        self.assertEquals(context_ids, db_ids)

        # I guess this just returns the same thing?
        response = self.client.get("/species/all/")
        self.assertTemplateUsed(response, 'treemap/species.html')

        context_ids = set([s.pk for s in response.context["species"]])
        self.assertEquals(context_ids, db_ids)

        # With 'json' in the query, do the same thing but return
        # JSON
        response = self.client.get("/species/all/json/")
        json_species = loads(response.content)

        json_ids = set([j['id'] for j in json_species])
        self.assertEqual(json_ids, db_ids)

        response = self.client.get("/species/json/")
        json_species = loads(response.content)

        json_ids = set([j['id'] for j in json_species])
        self.assertEqual(json_ids, db_ids)


    def test_inuse_species(self):
        # Start from a clean slate
        # Note- is it a bug that calling 'delete' on trees
        # doesn't update the species count?
        for t in Tree.objects.all():
            t.present = False
            t.save()
        for p in Plot.objects.all():
            p.present = False
            p.save()

        self.assertEqual(self.make_request("/species/in-use/"),
                         set([]))

        mkTree(self.u, species=self.s1)
        mkTree(self.u, species=self.s1)
        mkTree(self.u, species=self.s1)

        self.assertEqual(self.make_request("/species/in-use/"),
                         set([(self.s1.pk,3)]))

        mkTree(self.u, species=self.s1)
        mkTree(self.u, species=self.s2)
        mkTree(self.u, species=self.s3)
        mkTree(self.u, species=self.s3)

        self.assertEqual(self.make_request("/species/in-use/"),
                         set([(self.s1.pk,4),
                              (self.s2.pk,1),
                              (self.s3.pk,2)]))

    def make_request(self, url, body=None):
        # Force a commit for ogr2ogr conversions
        transaction.commit()

        if body is None:
            body = {}

        response_html = self.client.get(url, body)

        html_ids = set([(s.pk,s.tree_count) \
                        for s in response_html.context["species"]])
        response_json = self.client.get("%sjson/" % url, body)

        json_species = loads(response_json.content)
        json_ids = set([(s['id'],s['count']) for s in json_species])

        response_csv = self.client.get("%scsv/" % url, body)

        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['content-type'], 'application/zip')
        self.assertEqual(response_csv['content-disposition'],
                         'attachment; filename=species.zip')

        from zipfile import ZipFile
        from StringIO import StringIO
        from csv import DictReader

        zipdata = ZipFile(StringIO(response_csv.content))
        csv_ids = []
        for row in DictReader(zipdata.open('species./species..csv')):
            csv_ids.append((int(row['id']), int(row['tree_count'])))

        csv_ids = set(csv_ids)

        self.assertEqual(html_ids, json_ids)
        self.assertEqual(html_ids, csv_ids)
        return html_ids


    def test_nearby_species(self):
        # Start from a clean slate
        for t in Tree.objects.all():
            t.present = False
            t.save()
        for p in Plot.objects.all():
            p.present = False
            p.save()


        # If you don't specify a 'location' param you
        # get a 404....
        response = self.client.get("/species/nearby/")
        self.assertEqual(response.status_code, 404)

        def loc_request(x,y):
            url = "/species/nearby/"
            location = {'location': '%s,%s' % (x,y)}

            return self.make_request(url, location)

        def makeIt(x,y,s):
            mkTree(self.u,
                   plot=mkPlot(self.u,geom=Point(x,y)),
                   species=s)

        makeIt(35.00001,5.0,self.s1)
        makeIt(35.00002,5.0,self.s1)
        makeIt(35.00102,5.0,self.s1)
        makeIt(35.00102,5.0,self.s2)
        makeIt(45.00000,5.0,self.s2)
        makeIt(45.00000,5.0,self.s3)

        s1 = self.s1.pk
        s2 = self.s2.pk
        s3 = self.s3.pk

        self.assertEqual(loc_request(6,6),
                         set([]))

        # It appears that 'tree_count' is the entire
        # species count, even when doing a nearby query... not sure
        # if this is intentional but this encodes that specific logic
        self.assertEqual(loc_request(35.0,5.0),
                         set([(s1, 3)]))

        self.assertEqual(loc_request(35.0005,5.0),
                         set([(s1, 3),
                              (s2, 2)]))

        # Just FYI, There is a hardcoded constant of 0.001 for distance
        # so this test encodes that logic as well
        self.assertEqual(loc_request(35.000019,5.0),
                         set([(s1, 3)]))


class ViewTests(TestCase):

    def setUp(self):
        setupTreemapEnv()

        self.z1 = ZipCode.objects.get(zip="19107")
        self.n1 = Neighborhood.objects.get(name="n1")

        self.u = User.objects.get(username="jim")

        p1_no_tree = mkPlot(self.u, geom=Point(50,50))
        p2_tree = mkPlot(self.u, geom=Point(51,51))
        p3_tree_species1 = mkPlot(self.u, geom=Point(50,100))
        p4_tree_species2 = mkPlot(self.u, geom=Point(50,150))

        self.s1 = Species.objects.get(symbol="s1")
        self.s2 = Species.objects.get(symbol="s2")
        self.s3 = Species.objects.get(symbol="s3")

        t1 = mkTree(self.u, p2_tree, species=None)
        t2 = mkTree(self.u, p3_tree_species1, self.s1)
        t3 = mkTree(self.u, p4_tree_species2, self.s2)

        self.p1_no_tree = p1_no_tree
        self.p2_tree = p2_tree
        self.p3_tree_species1 = p3_tree_species1;
        self.p4_tree_species2 = p4_tree_species2;

        self.plots = [p1_no_tree, p2_tree, p3_tree_species1, p4_tree_species2]

        self.t1 = t1
        self.t2 = t2
        self.t3 = t3

        self.ie = ImportEvent.objects.get(file_name='site_add')



##############################################
#  Stewardship raw sql tests

    def test_stewardship(self):
        TreeStewardship.objects.create(activity="test",
                               tree=self.t1,
                               performed_by=self.u,
                               performed_date=datetime.now())

        # Two actions at different times
        TreeStewardship.objects.create(activity="test",
                               tree=self.t1,
                               performed_by=self.u,
                               performed_date=datetime.now())

        trees = Stewardship.trees_with_activities(["test2"])

        self.assertEqual(
            set(trees),
            set())

        TreeStewardship.objects.create(activity="test2",
                               tree=self.t1,
                               performed_by=self.u,
                               performed_date=datetime.now())

        trees = Stewardship.trees_with_activities(["test2"])

        TreeStewardship.objects.create(activity="test2",
                               tree=self.t2,
                               performed_by=self.u,
                               performed_date=datetime.now())

        trees = Stewardship.trees_with_activities(["test2"])

        self.assertEqual(
            set(trees),
            set([self.t1.pk, self.t2.pk]))

        trees = Stewardship.trees_with_activities(["test"])

        self.assertEqual(
            set(trees),
            set([self.t1.pk]))



##############################################
#  Assertion helpers

    def assert_geojson_has_ids(self, geojson, ids):
        return self.assertEqual(self.geojson_ft2id(geojson), ids)


    def assert_point_in_nhood(self, point, nhood):
        test_set = Neighborhood.objects.filter(geometry__contains=point)
        for t in test_set:
            if t == nhood:
                return
        self.fail("Point not in Neighborhood: %s" % nhood.name)



##############################################
#  Data conversion helpers

    def geojson_ft2id(self,geojson):
        if geojson and "features" in geojson:
            return set([int(ft["properties"]["id"]) for ft in geojson["features"]])
        else:
            return set()

#############################################
#  shortcut tests

    def test_add_initial_defaults(self):
        settings.ADD_INITIAL_DEFAULTS = {
            'dbh': "Size",
        }
        # the changed setting should show up
        self.assertEqual(get_add_initial('dbh'), 'Size')
        # an unchanged settings should be the default still
        self.assertEqual(get_add_initial('height'), '')

#############################################
#  page setup tests

    def test_homepage_feeds(self):
        response = self.client.get("/home/")
        self.assertTemplateUsed(response, 'treemap/index.html')
        response = self.client.get("/home/feeds/")
        self.assertTemplateUsed(response, 'treemap/index.html')
        feeds = response.context["feeds"]
        self.assertNotEqual(len(feeds["active_nhoods"]), 0)
        self.assertIsInstance(feeds["active_nhoods"][0], Neighborhood)
        self.assertNotEqual(len(feeds["species"]), 0)
        self.assertIsInstance(feeds["species"][0], Species)
        self.assertEqual(len(feeds["recent_photos"]), 0)
        self.assertNotEqual(len(feeds["recent_edits"]), 0)
        self.assertEqual(feeds["recent_edits"][0][0], u'jim')
        self.assertIsInstance(feeds["recent_edits"][0][1], datetime)

        response = self.client.get("/home/feeds/json/")
        json = loads(response.content)
        self.assertNotEqual(len(json["species"]), 0)
        self.assertNotEqual(len(json["active_nhoods"]), 0)


    def test_get_choices(self):
        response = self.client.get("/choices/")
        choices = loads(response.content)
        self.assertNotEqual(len(choices['plot_types']), 0)


#############################################
#  Geocoder Tests

    def test_geocoder(self):
        response = self.client.get("/geocode/")
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("No geocoder", json["error"])

        form = {}
        form["geocoder_name"] = "CitizenAtlas"
        response = self.client.get("/geocode/", form)
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("No address", json["error"])

        form["address"] = "100 somewhere"
        response = self.client.get("/geocode/", form)
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("No results", json["error"])

        form["address"] = "100 10th St SE"
        response = self.client.get("/geocode/", form)
        json = loads(response.content)
        self.assertTrue(json["success"])
        self.assertIn("10TH", json["place"])
        self.assertIn("20003", json["place"])
        self.assertAlmostEqual(float(json['lat']), 38.88857251)
        self.assertAlmostEqual(float(json['lng']), -76.99244160)

        #############################################
        #  reverse geocoding

        response = self.client.get("/geocode/reverse/")
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("No geocoder", json["error"])

        form = {}
        form["geocoder_name"] = "CitizenAtlas"
        response = self.client.get("/geocode/reverse/", form)
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("No point", json["error"])

        form["lat"] = "abc"
        form["lng"] = "def"
        response = self.client.get("/geocode/reverse/", form)
        json = loads(response.content)
        self.assertFalse(json["success"])
        self.assertIn("could not convert", json["error"])

        form["lat"] = 38.88857251
        form["lng"] = -76.99244160
        response = self.client.get("/geocode/reverse/", form)
        json = loads(response.content)
        self.assertTrue(json["success"])
        self.assertIn("10TH", json["place"])
        self.assertIn("20003", json["place"])
        self.assertAlmostEqual(float(json['lat']), form['lat'])
        self.assertAlmostEqual(float(json['lng']), form['lng'])


#############################################
#  Search Tests

    def test_plot_location_search_error_cases(self):
        """ Test error cases for plot location search """
         # The following errors should all be 400 -> Malformed Request

        # Error case -> Missing get data
        # Requires lat,lon or bbox
        response = self.client.get("/plots/location/")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/plots/location/?lat=-77")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/plots/location/?lon=-32")
        self.assertEqual(response.status_code, 400)


    def test_plot_location_search_pt(self):
        """ Test searching for plot by pt """
        reqstr = "/plots/location/?lat=%s&lon=%s&distance=%s&max_plots=%s"

        ##################################################################
        # Limit max plots to 1 - expect to get only 1 plot back
        response = self.client.get(reqstr % (50,50,1000,1))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p1_no_tree.pk]))

        ##################################################################
        # Limit distance to 5, expect to get only two (50,50) and (51,51) back
        response = self.client.get(reqstr % (50,50,5,100))
        geojson = loads(response.content)

        exp = set([self.p1_no_tree.pk, self.p2_tree.pk])

        self.assert_geojson_has_ids(geojson, exp)

        ##################################################################
        # Effective unlimited distance should return all plots
        response = self.client.get(reqstr % (50,50,10000,100))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([p.pk for p in self.plots]))

        ##################################################################
        # Species filter tests
        #
        # The following business rules apply:
        # -> If (as above) no species if specified, return all plots
        # -> If a species is specifed:
        #      AND results in matching one or more (based on distance)
        #      THEN return only those plots with trees with the given species

        reqstr = "/plots/location/?lat=50&lon=50&distance=1000&max_plots=100&species=%s"

        response = self.client.get(reqstr % (self.s1.pk))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p3_tree_species1.pk]))

        response = self.client.get(reqstr % (self.s2.pk))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p4_tree_species2.pk]))

        ##################################################################
        # -> If a species is specified:
        #      AND results in NO distance matches
        #      THEN return the original results, unfiltered
        #

        response = self.client.get(reqstr % (1000000))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([p.pk for p in self.plots]))

    def test_result_map(self):
        ##################################################################
        # Test main result map page
        # Note -> This page does not depend at all on the request
        #

        p1 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie,present=True, width=100, length=100, data_owner=self.u)
        p2 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=90, length=110, data_owner=self.u)

        p1.save()
        p2.save()

        # For max/min plot size
        p3 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie,present=True, width=80, length=120, data_owner=self.u)
        p4 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=70, length=130, data_owner=self.u)
        p5 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=60, length=70, data_owner=self.u)

        p3.save()
        p4.save()
        p5.save()

        t3 = Tree(plot=p3, species=None, last_updated_by=self.u, import_event=self.ie,present=True)
        t3.save()

        t4 = Tree(plot=p4, species=None, last_updated_by=self.u, import_event=self.ie,present=True)
        t4.save()

        t5 = Tree(plot=p5, species=None, last_updated_by=self.u, import_event=self.ie,present=True)
        t5.save()

        t1 = Tree(plot=p1, species=None, last_updated_by=self.u, import_event=self.ie)
        t1.present = True

        current_year = datetime.now().year
        t1.date_planted = date(1999,9,9)

        t2 = Tree(plot=p2, species=None, last_updated_by=self.u, import_event=self.ie)
        t1.present = True

        t1.save()
        t2.save()

        set_auto_now(t1, "last_updated", False)
        t1.last_updated = date(1999,9,9)
        t1.save()

        response = self.client.get("/map/")
        req = response.context


        set_auto_now(t1, "last_updated", True)

        # t1 and t2 should not be in the latest trees/plots because it excludes superuser edits
        exp = set([])
        got = set([t.pk for t in req['latest_trees']])

        self.assertTrue(exp <= got)

        got = set([t.pk for t in req['latest_plots']])
        self.assertTrue(exp <= got)

        # Check to verify platting dates
        self.assertEquals(int(req['min_year']), 1999)
        self.assertEquals(int(req['current_year']), current_year)

        # Correct min/max plot sizes
        self.assertEqual(int(req['min_plot']), 60)
        self.assertEqual(int(req['max_plot']), 130)

        min_updated = mktime(t1.last_updated.timetuple())
        max_updated = mktime(t2.last_updated.timetuple())

        self.assertEqual(req['min_updated'], min_updated)
        self.assertEqual(req['max_updated'], max_updated)
        # 'min_updated': min_updated,
        # 'max_updated': max_updated,

    def test_search_results(self):
        ##################################################################
        # Test search result view
        #

        def assert_counts(tree_count, plot_count, req):
            self.assertEqual(req['summaries']['total_trees'], tree_count)
            self.assertEqual(req['summaries']['total_plots'], plot_count)

        def assert_benefits(req, isEmpty=False):
            if isEmpty:
                self.assertEqual(req['benefits']['total'], 0.0)
            else:
                self.assertNotEqual(req['benefits']['total'], 0.0)

        def to_search_string(choice_name):
            return choice_name.lower().replace(" ", "_").replace('/','')

        oneDay = timedelta(days=1)
        oneYear = timedelta(days=365)
        date_min = datetime.utcnow() - oneDay
        date_max = datetime.utcnow()
        qs_date_min = time.mktime(date_min.timetuple())
        qs_date_max = time.mktime(date_max.timetuple())

        plot_type_choices = CHOICES['plot_types']
        sidewalk_choices = CHOICES['sidewalks']
        powerline_choices = CHOICES['powerlines']
        tsteward_choices = CHOICES['tree_stewardship']
        psteward_choices = CHOICES['plot_stewardship']
        condition_choices = CHOICES['conditions']
        flag_choices = CHOICES['projects']

        p1 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie, type=plot_type_choices[0][0],width=1, length=1, data_owner=self.u)
        p2 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie, type=plot_type_choices[1][0], width=3, length=5, data_owner=self.u)
        p3 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie, width=10, length=15, data_owner=self.u)
        p4 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie, sidewalk_damage=sidewalk_choices[0][0], data_owner=self.u)
        p5 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie, powerline_conflict_potential=powerline_choices[1][0], data_owner=self.u)
        p6 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie, data_owner=self.u)

        save_this = [p1,p2,p3,p4,p5,p6]
        for obj in save_this: obj.save()

        t1 = Tree(plot=p1, last_updated_by=self.u, import_event=self.ie, dbh=4, condition=condition_choices[0][0], date_planted=datetime.utcnow()-oneYear)
        t2 = Tree(plot=p2, last_updated_by=self.u, import_event=self.ie, dbh=10, species=self.s1, condition=condition_choices[1][0])
        t3 = Tree(plot=p3, last_updated_by=self.u, import_event=self.ie, dbh=40, species=self.s1, height=150, sponsor=self.u.username, date_planted=date_min)
        t4 = Tree(plot=p4, last_updated_by=self.u, import_event=self.ie, height=30, species=self.s3, condition=condition_choices[3][0], steward_user=self.u)
        t5 = Tree(plot=p6, last_updated_by=self.u, import_event=self.ie, dbh=30, species=self.s3)

        ps1 = PlotStewardship(performed_by=self.u, performed_date=datetime.now(), plot=p1, activity=psteward_choices[0][0])
        ps2 = PlotStewardship(performed_by=self.u, performed_date=datetime.now(), plot=p2, activity=psteward_choices[1][0])
        ps3 = PlotStewardship(performed_by=self.u, performed_date=datetime.now(), plot=p2, activity=psteward_choices[2][0])

        save_this = [ps1,ps2,ps3, t1,t2,t3,t4,t5]
        for obj in save_this: obj.save()

        tf1 = TreeFlags(reported_by=self.u, tree=t1, key=flag_choices[0][0])
        tf2 = TreeFlags(reported_by=self.u, tree=t4, key=flag_choices[0][0])

        ts1 = TreeStewardship(performed_by=self.u, performed_date=datetime.now(), tree=t1, activity=tsteward_choices[0][0])
        ts2 = TreeStewardship(performed_by=self.u, performed_date=datetime.now(), tree=t2, activity=tsteward_choices[1][0])
        ts3 = TreeStewardship(performed_by=self.u, performed_date=datetime.now(), tree=t2, activity=tsteward_choices[2][0])

        save_this = [tf1,tf2, ts1,ts2,ts3]
        for obj in save_this: obj.save()

        response = self.client.get("/search/")
        req = loads(response.content)

        present_trees = Tree.objects.filter(present=True)
        present_plots = Plot.objects.filter(present=True)

        assert_counts(present_trees.count(), present_plots.count(), req)
        assert_benefits(req)
        self.assertEqual(req['full_tree_count'], present_trees.count())
        self.assertEqual(req['full_plot_count'], present_plots.count())
        self.assertEqual(req['tile_query'], '')
        self.assertEqual(req['geography'], None)

        ##################################################################
        # Test geographic searches
        #    neighborhood, zipcode, lat/lon
        #
        response = self.client.get("/search/?geoName=%s" % self.n1.name )
        req = loads(response.content)
        trees = present_trees.filter(plot__neighborhood=self.n1)
        plots = present_plots.filter(neighborhood=self.n1)
        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertEqual(req['geography']['type'], 'Polygon')
        self.assertEqual(req['geography']['name'], self.n1.name)
        self.assertTrue('neighborhoods' in req['tile_query'])

        response = self.client.get("/search/?location=%s" % self.z1.zip)
        req = loads(response.content)
        trees = present_trees.filter(plot__zipcode=self.z1)
        plots = present_plots.filter(zipcode=self.z1)
        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertEqual(req['geography']['type'], 'Polygon')
        self.assertEqual(req['geography']['name'], self.z1.zip)
        self.assertTrue('zipcode' in req['tile_query'])

        response = self.client.get("/search/?lat=%d&lon=%d" % (25.0,25.0))
        req = loads(response.content)
        nbhood = Neighborhood.objects.filter(geometry__contains=Point(25,25))[0]
        trees = present_trees.filter(plot__zipcode=nbhood)
        plots = present_plots.filter(zipcode=nbhood)
        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertEqual(req['geography']['type'], 'Polygon')
        self.assertEqual(req['geography']['name'], nbhood.name)
        self.assertTrue('neighborhoods' in req['tile_query'])

        ##################################################################
        # Test plot data searches
        #    plot type, plot size, sidewalk damage, powerlines, owner,
        #    plot stewardship
        #
        plot_list = [1, 2]
        plot_name_list = [to_search_string(plot_type_choices[0][1]),to_search_string(plot_type_choices[1][1])]
        response = self.client.get("/search/?%s=true&%s=true" % (plot_name_list[0], plot_name_list[1]))
        req = loads(response.content)
        trees = present_trees.filter(plot__type__in=plot_list)
        plots = present_plots.filter(type__in=plot_list)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_type' in req['tile_query'])

        plot_range = [3, 11]
        response = self.client.get("/search/?plot_range=%s-%s" % (plot_range[0], plot_range[1]) )
        req = loads(response.content)
        trees = present_trees.filter(Q(plot__length__gte=plot_range[0]) | Q(plot__width__gte=plot_range[0])).filter(Q(plot__length__lte=plot_range[1]) | Q(plot__width__lte=plot_range[1]))
        plots = present_plots.filter(Q(length__gte=plot_range[0]) | Q(width__gte=plot_range[0])).filter(Q(length__lte=plot_range[1]) | Q(width__lte=plot_range[1]))

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_width' in req['tile_query'])
        self.assertTrue('plot_length' in req['tile_query'])

        sidewalk_list = [1]
        response = self.client.get("/search/?%s=true" % (to_search_string(sidewalk_choices[0][1])) )
        req = loads(response.content)
        trees = present_trees.filter(plot__sidewalk_damage__in=sidewalk_list)
        plots = present_plots.filter(sidewalk_damage__in=sidewalk_list)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('sidewalk_damage' in req['tile_query'])

        powerline_list = [2]
        response = self.client.get("/search/?%s=true" % (to_search_string(powerline_choices[1][1])) )
        req = loads(response.content)
        trees = present_trees.filter(plot__powerline_conflict_potential__in=powerline_list)
        plots = present_plots.filter(powerline_conflict_potential__in=powerline_list)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('powerline' in req['tile_query'])

        response = self.client.get("/search/?owner=%s" % self.u.username)
        req = loads(response.content)
        users = User.objects.filter(username__icontains=self.u.username)
        trees = present_trees.filter(plot__data_owner__in=users)
        plots = present_plots.filter(data_owner__in=users)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('data_owner' in req['tile_query'])

        plot_stewardship_list = [1,2]
        response = self.client.get("/search/?plot_stewardship=%s,%s&stewardship_range=%s-%s&stewardship_reverse=true" % (plot_stewardship_list[0], plot_stewardship_list[1], qs_date_min, qs_date_max) )
        req = loads(response.content)
        steward_ids = [s.plot_id for s in PlotStewardship.objects.order_by("plot__id").distinct("plot__id")]
        for ps in plot_stewardship_list:
            steward_ids = [s.plot_id for s in PlotStewardship.objects.filter(plot__id__in=steward_ids).filter(activity=ps)]
        plots = present_plots.filter(id__in=steward_ids).exclude(plotstewardship__performed_date__lte=date_min).exclude(plotstewardship__performed_date__gte=date_max)
        trees = present_trees.filter(plot__in=plots)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('plot_stewardship' in req['tile_query'])

        response = self.client.get("/search/?plot_stewardship=%s,%s&stewardship_range=%s-%s&stewardship_reverse=false" % (plot_stewardship_list[0],plot_stewardship_list[1], qs_date_min, qs_date_max) )
        req = loads(response.content)
        plots = present_plots.exclude(id__in=steward_ids).exclude(plotstewardship__performed_date__lte=date_min).exclude(plotstewardship__performed_date__gte=date_max)
        trees = present_trees.filter(plot__in=plots)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_stewardship' in req['tile_query'])

        ##################################################################
        # Test tree data searches
        #    diameter, height, condition, photos, steward, sponsor
        #    projects, planted date range, tree stewardship
        #
        diameter_list = [11,25]
        response = self.client.get("/search/?diameter_range=%s-%s" % (diameter_list[0],diameter_list[1]) )
        req = loads(response.content)
        trees = present_trees.filter(dbh__gte=diameter_list[0]).filter(dbh__lte=diameter_list[1])
        plots = present_plots.filter(tree__dbh__gte=diameter_list[0]).filter(tree__dbh__lte=diameter_list[1])

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('dbh' in req['tile_query'])

        height_list = [0,50]
        response = self.client.get("/search/?height_range=%s-%s" % (height_list[0],height_list[1]) )
        req = loads(response.content)
        trees = present_trees.filter(height__gte=height_list[0]).filter(height__lte=height_list[1])
        plots = present_plots.filter(tree__height__gte=height_list[0]).filter(tree__height__lte=height_list[1])

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('height' in req['tile_query'])

        condition_list = [1,2]
        response = self.client.get("/search/?%s=true&%s=true" % (to_search_string(condition_choices[0][1]), to_search_string(condition_choices[1][1])) )
        req = loads(response.content)
        trees = present_trees.filter(condition__in=condition_list)
        plots = present_plots.filter(tree__condition__in=condition_list)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('condition' in req['tile_query'])

        response = self.client.get("/search/?photos=true" )
        req = loads(response.content)
        trees = present_trees.filter(treephoto__isnull=False)
        plots = present_plots.filter(tree__treephoto__isnull=False)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('photo_count' in req['tile_query'])

        response = self.client.get("/search/?steward=%s" % self.u.username)
        req = loads(response.content)
        users = User.objects.filter(username__icontains=self.u.username)
        trees = present_trees.filter(Q(steward_user__in=users) | Q(steward_name__icontains=self.u.username))
        plots = present_plots.filter(Q(tree__steward_user__in=users) | Q(tree__steward_name__icontains=self.u.username))

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('steward_user_id' in req['tile_query'])
        self.assertTrue('steward_name' in req['tile_query'])

        response = self.client.get("/search/?funding=%s" % self.u.username)
        req = loads(response.content)
        trees = present_trees.filter(sponsor__icontains=self.u.username)
        plots = present_plots.filter(tree__sponsor__icontains=self.u.username)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('sponsor' in req['tile_query'])

        planted_range_list = ["2010-01-01","2012-12-31"]
        response = self.client.get("/search/?planted_range=2010-2012" )
        req = loads(response.content)
        trees = present_trees.filter(date_planted__gte=planted_range_list[0], date_planted__lte=planted_range_list[1])
        plots = present_plots.filter(tree__date_planted__gte=planted_range_list[0], tree__date_planted__lte=planted_range_list[1])

        assert_counts(trees.count(), plots.count(), req)
        # This test is broken. A tree without a species cannot
        # have an ecobenefit, so this assertion is broken:
        # assert_benefits(req)
        self.assertTrue('date_planted' in req['tile_query'])

        local_list = [1, 2]
        response = self.client.get("/search/?%s=true&%s=true" % (to_search_string(flag_choices[0][1]), to_search_string(flag_choices[1][1])) )
        req = loads(response.content)
        trees = present_trees.filter(treeflags__key__in=local_list)
        plots = present_plots.filter(tree__treeflags__key__in=local_list)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('projects' in req['tile_query'])

        tree_stewardship_list = [1,2]
        response = self.client.get("/search/?tree_stewardship=%s,%s&stewardship_range=%s-%s&stewardship_reverse=true" % (tree_stewardship_list[0], tree_stewardship_list[1], qs_date_min, qs_date_max) )
        req = loads(response.content)
        steward_ids = [s.tree_id for s in TreeStewardship.objects.order_by("tree__id").distinct("tree__id")]
        for ts in tree_stewardship_list:
            steward_ids = [s.tree_id for s in TreeStewardship.objects.filter(tree__id__in=steward_ids).filter(activity=ts)]
        trees = present_trees.filter(id__in=steward_ids).exclude(treestewardship__performed_date__lte=date_min).exclude(treestewardship__performed_date__gte=date_max)
        plots = present_plots.filter(tree__in=trees)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('tree_stewardship' in req['tile_query'])

        response = self.client.get("/search/?tree_stewardship=%s,%s&stewardship_range=%s-%s&stewardship_reverse=false" % (tree_stewardship_list[0],tree_stewardship_list[1], qs_date_min, qs_date_max) )
        req = loads(response.content)
        trees = present_trees.exclude(id__in=steward_ids).exclude(treestewardship__performed_date__lte=date_min).exclude(treestewardship__performed_date__gte=date_max)
        plots = present_plots.filter(tree__in=trees)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('tree_stewardship' in req['tile_query'])

        ##################################################################
        # Test species data searches
        #    id, native, edible, fall color, flowering, wildlife
        #
        present_species = Species.objects.filter(tree_count__gt=0)
        def check_species(species_list, req):
            max_species = present_species.count()
            trees = present_trees.filter(species__in=species_list)
            plots = present_plots.filter(tree__species__in=species_list)

            assert_counts(trees.count(), plots.count(), req)
            if max_species != species_list.count():
                self.assertTrue('species_id' in req['tile_query'])

        response = self.client.get("/search/?species=%s" % self.s1.id )
        req = loads(response.content)
        species = present_species.filter(id=self.s1.id)
        check_species(species, req)
        assert_benefits(req)

        response = self.client.get("/search/?native=true" )
        req = loads(response.content)
        species = present_species.filter(native_status='True')
        check_species(species, req)
        assert_benefits(req)

        response = self.client.get("/search/?edible=true" )
        req = loads(response.content)
        species = present_species.filter(palatable_human=True)
        check_species(species, req)
        assert_benefits(req)

        response = self.client.get("/search/?color=true" )
        req = loads(response.content)
        species = present_species.filter(fall_conspicuous=True)
        check_species(species, req)
        assert_benefits(req)

        response = self.client.get("/search/?flowering=true" )
        req = loads(response.content)
        species = present_species.filter(flower_conspicuous=True)
        check_species(species, req)
        assert_benefits(req)

        response = self.client.get("/search/?wildlife=true" )
        req = loads(response.content)
        species = present_species.filter(wildlife_value=True)
        check_species(species, req)
        assert_benefits(req)

        ##################################################################
        # Test plot/tree data searches
        #    updated by, updated range
        #    - These test search both trees and plots in the same way
        #
        response = self.client.get("/search/?updated_by=%s" % self.u.username)
        req = loads(response.content)
        users = User.objects.filter(username__icontains=self.u.username)
        trees = present_trees.filter(last_updated_by__in=users)
        plots = present_plots.filter(last_updated_by__in=users)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('last_updated_by' in req['tile_query'])

        response = self.client.get("/search/?updated_range=%s-%s" % (qs_date_min, qs_date_max) )
        req = loads(response.content)
        trees = present_trees.filter(last_updated__gte=date_min, last_updated__lte=date_max)
        plots = present_plots.filter(last_updated__gte=date_min, last_updated__lte=date_max)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('last_updated' in req['tile_query'])


        ##################################################################
        # Test missing data searches
        #    species, diameter, height, plot type, plot size, condition,
        #    sidewalk damage, powerlines, photos
        #    - Some searches count 0 values as 'missing'
        #
        response = self.client.get("/search/?missing_species=true")
        req = loads(response.content)

        trees = present_trees.filter(species__isnull=True)
        plots = present_plots.filter(tree__species__isnull=True)
        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('species_id' in req['tile_query'])

        response = self.client.get("/search/?missing_diameter=true")
        req = loads(response.content)
        trees = present_trees.filter(Q(dbh__isnull=True) | Q(dbh=0))
        plots = present_plots.filter(Q(tree__dbh__isnull=True) | Q(tree__dbh=0))

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req, True)
        self.assertTrue('dbh' in req['tile_query'])

        response = self.client.get("/search/?missing_height=true")
        req = loads(response.content)
        trees = present_trees.filter(Q(height__isnull=True) | Q(height=0))
        plots = present_plots.filter(Q(tree__height__isnull=True) | Q(tree__height=0))

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('height' in req['tile_query'])

        response = self.client.get("/search/?missing_plot_type=true")
        req = loads(response.content)
        trees = present_trees.filter(plot__type__isnull=True)
        plots = present_plots.filter(type__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_type' in req['tile_query'])

        response = self.client.get("/search/?missing_plot_size=true")
        req = loads(response.content)
        trees = present_trees.filter(Q(plot__length__isnull=True) | Q(plot__width__isnull=True))
        plots = present_plots.filter(Q(length__isnull=True) | Q(width__isnull=True))

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_length' in req['tile_query'])

        response = self.client.get("/search/?missing_condition=true")
        req = loads(response.content)
        trees = present_trees.filter(condition__isnull=True)
        plots = present_plots.filter(tree__condition__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('condition' in req['tile_query'])

        response = self.client.get("/search/?missing_sidewalk=true")
        req = loads(response.content)
        trees = present_trees.filter(plot__sidewalk_damage__isnull=True)
        plots = present_plots.filter(sidewalk_damage__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('sidewalk_damage' in req['tile_query'])

        response = self.client.get("/search/?missing_powerlines=true")
        req = loads(response.content)
        trees = present_trees.filter(plot__powerline_conflict_potential__isnull=True)
        plots = present_plots.filter(powerline_conflict_potential__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('powerline_conflict_potential' in req['tile_query'])

        response = self.client.get("/search/?missing_photos=true")
        req = loads(response.content)
        trees = present_trees.filter(treephoto__isnull=True)
        plots = present_plots.filter(tree__treephoto__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('photo_count' in req['tile_query'])

        ##################################################################
        # Test searching precedance rules
        #    - Missing data search trumps data search
        #    - Missing species + species id = 0 results
        #
        response = self.client.get("/search/?missing_plot_type=true&tree_pit=true")
        req = loads(response.content)
        trees = present_trees.filter(plot__type__isnull=True)
        plots = present_plots.filter(type__isnull=True)

        assert_counts(trees.count(), plots.count(), req)
        assert_benefits(req)
        self.assertTrue('plot_type' in req['tile_query'])

        response = self.client.get("/search/?missing_species=true&species=%s" % self.s1.id)
        req = loads(response.content)

        assert_counts(0,0, req)
        assert_benefits(req, True)
        self.assertTrue('species_id' in req['tile_query'])


#############################################
#  New Plot Tests

    def test_add_plot(self):
        self.client.login(username='jim',password='jim')
        form = {}
        form['target']="view"
        form['initial_map_location'] = "20,20"
        ##################################################################
        # Test required information:
        #     lat,lon,entered address and geocoded address

        form['lat'] = 1000
        form['lon'] = 1000
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        del form['lat']
        del form['lon']
        form['lat'] = 50
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['lon'] = 50
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['edit_address_street'] = "100 N Broad"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        del form['edit_address_street']
        form['geocode_address'] = "100 N Broad St"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['edit_address_street'] = "100 N Broad"

        response = self.client.post("/trees/add/", form)
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response["Location"].endswith('/trees/new/%i/' % self.u.id), "Expected Location header to end with /trees/new/\d+ but instead it was %s" % response["Location"])

        response = self.client.get('/trees/new/%i/' % self.u.id)
        self.assertNotEqual(len(response.context['plots']), 0)
        new_plot = response.context['plots'][0]
        self.assertTrue(new_plot.geocoded_address, form['geocode_address'])

        response = self.client.get('/trees/new/%i/geojson/' % self.u.id)
        json_plots = loads(response.content)
        self.assertEqual(json_plots[0]['id'], new_plot.id)

        new_plot = None

        ##################################################################
        # Test plot-only creation:
        #     Info in these fields creates a plot object, and does not
        #     create a tree object

        form['edit_address_city'] = "Philadelphia"
        form['edit_address_zip'] = "19107"
        form['plot_width'] = "50"   #bad
        form['plot_width_in'] = "0"
        form['plot_length'] = "6"
        form['plot_length_in'] = "6"
        form['plot_type'] = "Open"
        form['power_lines'] = 1
        form['sidewalk_damage'] = 1

        # plot width < 15
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['plot_width'] = "5"
        # plot width inches < 12
        form['plot_width_in'] = "20"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['plot_width_in'] = "6"
        # plot type in type list
        form['plot_type'] = "Blargh"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['plot_type'] = 1
        # powerlines = 1, 2, or 3
        form['power_lines'] = 15
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['power_lines'] = 1
        # sidewalk damage = 1, 2, or 3
        form['sidewalk_damage'] = 15
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['sidewalk_damage'] = 1
        form['owner_additional_id'] = 111

        response = self.client.post("/trees/add/", form)
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)

        response = self.client.get('/trees/new/%i/' % self.u.id)
        new_plot = response.context['plots'][0]
        self.assertAlmostEqual(new_plot.width, 5.5)
        self.assertAlmostEqual(new_plot.length, 6.5)
        self.assertEqual(new_plot.current_tree(), None)
        self.assertEqual(new_plot.zipcode, self.z1)
        self.assert_point_in_nhood(new_plot.geometry, self.n1)

        new_plot = None

        ##################################################################
        # Test exclusion zones:
        #     Turn on exclusions in the settings and move point into exclusion zone

        form['lat'] = 20
        form['lon'] = 20
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')

        form['lat'] = 50
        form['lon'] = 50

        ##################################################################
        # Test tree creation:
        #     Info in the rest of the fields creates a tree object as well as a plot

        form['species_id'] = self.s1.id
        form['species_other1'] = 'newgenus'
        form['species_other2'] = 'newspecies'
        form['height'] = 50
        form['canopy_height'] = 40
        form['dbh'] = 2
        form['dbh_type'] = "circumference"
        form['condition'] = "Good"
        form['canopy_condition'] = "Full - No Gaps"

        # height <= 300
        form['height'] = 500
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['height'] = 60
        # canopy height <= 300
        form['canopy_height'] = 550
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        # canopy height <= height
        form['canopy_height'] = 80
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['canopy_height'] = 40
        # condition in list
        form['condition'] = "Blah"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['condition'] = 1
        # canopy condition in list
        form['canopy_condition'] = "Blah"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
        form['canopy_condition'] = 1

        response = self.client.post("/trees/add/", form)
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)

        # diameter instead
        del form['dbh_type']
        # no species
        del form['species_id']

        response = self.client.post("/trees/add/", form)
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)

        form['species_id'] = self.s1.pk

        response = self.client.post("/trees/add/", form)
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)

        response = self.client.get('/trees/new/%i/' % self.u.id)
        new_plot = response.context['plots'][2]   #first one created
        new_tree = new_plot.current_tree()
        self.assertNotEqual(new_tree, None)
        self.assertEqual(new_tree.species.genus, "testus1")
        self.assertAlmostEqual(new_tree.dbh, 2/math.pi)
        self.assertEqual(new_tree.plot, new_plot)

        # make sure the tree created benefit data and that it's not empty
        tr = TreeResource.objects.get(tree=new_tree)
        self.assertNotEqual(tr, None)
        self.assertNotEqual(tr.get_benefits()['total'], 0.0)

    def test_add_empty_tree(self):
        c = self.client
        c.login(username='jim',password='jim')
        orig_rep = User.objects.filter(username='jim')[0].reputation.reputation

        response = c.get("/plots/%i/addtree/" % self.p1_no_tree.id)
        json_status = loads(response.content)
        self.assertEquals(json_status['status'], "success")
        self.assertNotEquals(orig_rep, User.objects.filter(username='jim')[0].reputation.reputation)
        self.assertNotEquals(self.p1_no_tree.current_tree(), None)
        tree = self.p1_no_tree.current_tree()
        self.assertEquals(tree.last_updated_by.username, "jim")
        self.assertEquals(tree.species, None)


    def test_update_plot_no_pending(self):
        settings.PENDING_ON = False
        ##################################################################
        # Test edit page
        #
        # Expected POST params:
        # JSON dictionary of key-value pairs to update on a given plot object

        c = self.client

        p = self.p1_no_tree

        #
        # Test - Login redirect required
        #
        response = c.get("/plots/%s/update/" % p.pk)
        self.assertEqual(response.status_code, 302)

        login = c.login(username="jim",password="jim")

        #
        # Test - not sending a POST should fail
        #
        response = c.get("/plots/%s/update/" % p.pk)

        self.assertEqual(response.status_code, 405)

        #
        # Test - update all 'valid' fields
        #
        p.present = True
        p.width = 100
        p.length = 200
        p.type = "1"
        p.powerline_conflict_potential = "1"
        p.sidewalk_damange = "1"
        p.address_street = "100 Beach St"
        p.address_city = "Philadelphia"
        p.address_zip = "19103"
        p.save()

        response = c.post("/plots/%s/update/" % p.pk, { "width": "150", "length": "240",
                                                        "type": "4", "present": "False",
                                                        "powerline_conflict_potential": "3",
                                                        "sidewalk_damage": "2",
                                                        "address_street": "200 Lake Ave",
                                                        "address_city": "Avondale",
                                                        "address_zip": "23323" })

        p = Plot.objects.get(pk=p.pk)

        self.assertEqual(p.present, False)
        self.assertEqual(p.width, 150)
        self.assertEqual(p.length, 240)
        self.assertEqual(p.type, "4")
        self.assertEqual(p.powerline_conflict_potential, "3")
        self.assertEqual(p.sidewalk_damage, "2")
        self.assertEqual(p.address_street, "200 Lake Ave")
        self.assertEqual(p.address_city, "Avondale")
        self.assertEqual(p.address_zip, "23323")

        #
        # Test - update an invalid field and a valid field
        # verify neither gets written
        #
        p.present = True
        p.width = 120
        p.save()

        response = c.post("/plots/%s/update/" % p.pk, { "present": False,
                                                        "width": 200,
                                                        "geocoded_address": "blah" })

        self.assertEqual(p.present, True)
        self.assertEqual(p.width, 120)


        response_dict = loads(response.content)
        self.assertEqual(len(response_dict["errors"]), 1)
        self.assertTrue("geocoded_address" in response_dict["errors"][0])

        #
        # Test - validation error
        # verify neither gets written
        #
        p.present = True
        p.width = 120
        p.length = 220
        p.save()

        response = c.post("/plots/%s/update/" % p.pk, { "present": False,
                                                        "width": "200",
                                                        "length": "test" })

        self.assertEqual(p.present, True)
        self.assertEqual(p.width, 120)
        self.assertEqual(p.length, 220)

        response_dict = loads(response.content)
        self.assertEqual(len(response_dict["errors"]), 1)
        self.assertTrue("length" in response_dict["errors"][0])

    def test_update_plot_pending(self):
        settings.PENDING_ON = True
        ##################################################################
        # Test edit page
        #
        # Expected POST params:
        # -> model  - name of the model to update
        # -> id     - record id to update
        # -> update - dict of fields to update with value
        # -> parent - model/id the posted data should be added to

        c = self.client
        c.login(username='amy',password='amy')

        p = self.p1_no_tree

        #
        # Test - update all 'valid' fields and nothing
        # will be saved (instead pending records will be created)
        #
        p.present = True
        p.width = 100
        p.length = 200
        p.type = "1"
        p.powerline_conflict_potential = "1"
        p.sidewalk_damage = "1"
        p.address_street = "100 Beach St"
        p.address_city = "Philadelphia"
        p.address_zip = "19103"
        p.save()

        response = c.post("/plots/%s/update/" % p.pk, { "width": "150", "length": "240",
                                                        "type": "4", "present": "False",
                                                        "powerline_conflict_potential": "3",
                                                        "sidewalk_damage": "2",
                                                        "address_street": "200 Lake Ave",
                                                        "address_city": "Avondale",
                                                        "address_zip": "23323" })

        p = Plot.objects.get(pk=p.pk)

        self.assertTrue(len(p.get_active_pends()) > 0, 'Pends were created')

        self.assertEqual(p.present, True)
        self.assertEqual(p.width, 100)
        self.assertEqual(p.length, 200)
        self.assertEqual(p.type, "1")
        self.assertEqual(p.powerline_conflict_potential, "1")
        self.assertEqual(p.sidewalk_damage, "1")
        self.assertEqual(p.address_street, "100 Beach St")
        self.assertEqual(p.address_city, "Philadelphia")
        self.assertEqual(p.address_zip, "19103")

    def test_approve_plot_pending(self):
        settings.PENDING_ON = True

        p = self.p1_no_tree
        p.width = 100
        p.save()

        c = self.client
        c.login(username='amy', password='amy')

        response = c.post("/plots/%s/update/" % p.pk, { "width": "150"})
        self.assertEqual(response.status_code, 200, "Non 200 response when updating plot")

        p = Plot.objects.get(pk=p.pk)
        self.assertEqual(p.width, 100)

        pend = p.get_active_pends()[0]

        c.login(username='jim', password='jim')
        response = c.post("/trees/pending/%s/approve/" % pend.pk)
        self.assertEqual(response.status_code, 200, "Non 200 response when approving the pend")
        self.assertEqual(0, len(list(p.get_active_pends())), "Expected there to be zero pending edits after approval")

    def test_approve_plot_pending_with_mutiple_pending_edits(self):
        settings.PENDING_ON = True

        p = self.p1_no_tree
        p.width = 100
        p.length = 50
        p.save()

        c = self.client
        c.login(username='amy', password='amy')

        # First pending edit
        response = c.post("/plots/%s/update/" % p.pk, { "width": "150"})
        self.assertEqual(response.status_code, 200, "Non 200 response when updating plot")

        # Second pending edit to the same field
        response = c.post("/plots/%s/update/" % p.pk, { "width": "175"})
        self.assertEqual(response.status_code, 200, "Non 200 response when updating plot")

        # pending edit to a different field
        response = c.post("/plots/%s/update/" % p.pk, { "length": "25"})
        self.assertEqual(response.status_code, 200, "Non 200 response when updating plot")

        p = Plot.objects.get(pk=p.pk)
        self.assertEqual(3, len(list(p.get_active_pends())), "Expected three pending edits")

        pend = p.get_active_pends()[0]
        approved_pend_id = pend.id

        c.login(username='jim', password='jim')
        response = c.post("/trees/pending/%s/approve/" % pend.pk)
        self.assertEqual(response.status_code, 200, "Non 200 response when approving the pend")
        self.assertEqual(1, len(list(p.get_active_pends())), "Expected there to be 1 pending edits after approval, the length pend.")

        for plot_pending in PlotPending.objects.all():
            if plot_pending.id == approved_pend_id:
                self.assertEqual('approved', plot_pending.status, 'The status of the approved pend should be "approved"')
            elif plot_pending.field == 'width':
                self.assertEqual('rejected', plot_pending.status, 'The status of the non-approved width pends should be "rejected"')
            else: # plot_pending.id != approved_pend_id and plot_pending.field != 'width'
                self.assertEqual('pending', plot_pending.status, 'The status of pends not on the width field should still be "pending"')

    def test_need_permission_to_approve_pending(self):
        settings.PENDING_ON = True

        p = self.p1_no_tree
        p.width = 100
        p.save()

        c = self.client
        c.login(username='amy', password='amy')

        response = c.post("/plots/%s/update/" % p.pk, { "width": "150"})
        self.assertEqual(response.status_code, 200, "Non 200 response when updating plot")

        p = Plot.objects.get(pk=p.pk)
        self.assertEqual(p.width, 100)

        pend = p.get_active_pends()[0]

        response = c.post("/trees/pending/%s/approve/" % pend.pk)
        self.assertEqual(response.status_code, 403, "The request should have returned 403 forbidden")

##################################################################
# ogr conversion tests
#
    def assert_zip_response_contains_files(self, response, files):
        tmp_dir = tempfile.mkdtemp()
        tmp_file = os.path.join(tmp_dir, "attachment.zip")
        f = open(tmp_file, 'w')
        f.write(response.content)
        f.close()
        is_zipfile = zipfile.is_zipfile(tmp_file)
        self.assertTrue(is_zipfile, msg='error: %s does not look like a zip file.' % tmp_file)

        zf = zipfile.ZipFile(tmp_file, 'r')

        file_lists_match = (sorted(files) == sorted(zf.namelist()))
        self.assertTrue(file_lists_match,
            msg="error: file list in %s is: %s but I expected: %s" % (tmp_file, sorted(zf.namelist()), sorted(files)))

        zf.close()

        if (file_lists_match and is_zipfile): # leave the tmp file in case of an error.
            shutil.rmtree(tmp_dir)

        return


    def test_ogr_search_csv(self):
        response = self.client.get("/search/csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')
        self.assertEqual(response['content-disposition'], 'attachment; filename=trees.zip')
        self.assertNotEqual(len(response.content), 0)
        self.assert_zip_response_contains_files(response, ["eco.csv", "trees.csv", "plots.csv", 'species.csv'])

    def test_ogr_search_kml(self):
        response = self.client.get("/search/kml/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')
        self.assertEqual(response['content-disposition'], 'attachment; filename=trees.zip')
        self.assertNotEqual(len(response.content), 0)
        self.assert_zip_response_contains_files(response, ["eco.kml", "trees.kml", "plots.kml"])

    def test_ogr_search_shp(self):
        response = self.client.get("/search/shp/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')
        self.assertEqual(response['content-disposition'], 'attachment; filename=trees.zip')
        self.assertNotEqual(len(response.content), 0)
        self.assert_zip_response_contains_files(response, [
                "eco.dbf", "eco.prj", "eco.shp", "eco.shx",
                "plots.dbf", "plots.prj", "plots.shp",
                "plots.shx", "trees.dbf", "trees.prj",
                ])

    def test_ogr_comments_all_csv(self):
        # Test the admin-only exports
        c = self.client
        login = c.login(username="jim",password="jim")

        response = c.get("/comments/all/csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')
        self.assertEqual(response['content-disposition'], 'attachment; filename=comments.zip')
        self.assertNotEqual(len(response.content), 0)
        self.assert_zip_response_contains_files(response, ["comments.csv"])

    def test_ogr_users_optin_csv(self):
        # Test the admin-only exports
        c = self.client
        login = c.login(username="jim",password="jim")
        response = c.get("/users/opt-in/csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')
        self.assertEqual(response['content-disposition'], 'attachment; filename=emails.zip')
        self.assertNotEqual(len(response.content), 0)
        self.assert_zip_response_contains_files(response, ["emails.csv"])

##################################################################
# Tree/Plot Detail tests
#

    def test_tree_details(self):
        response = self.client.get('/trees/%i/' % 9999)
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/trees/%i/' % self.t3.id)
        self.assertTemplateUsed(response, 'treemap/tree_detail.html')
        self.assertIs(type(response.context['tree']), Tree)
        self.assertIs(type(response.context['plot']), Plot)
        self.assertEqual(response.context['tree'].id, self.t3.id)
        self.assertEqual(response.context['plot'].id, self.t3.plot.id)

    def test_plot_details(self):
        response = self.client.get('/plots/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/plots/%i/' % 9999)
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/plots/%i/' % self.p2_tree.id)
        self.assertTemplateUsed(response, 'treemap/tree_detail.html')
        self.assertIs(type(response.context['tree']), Tree)
        self.assertIs(type(response.context['plot']), Plot)
        self.assertEqual(response.context['tree'].id, self.p2_tree.current_tree().id)
        self.assertEqual(response.context['plot'].id, self.p2_tree.id)

        plot_format = {'format':'popup'}
        response = self.client.get('/plots/%i/' % self.p2_tree.id, plot_format)
        self.assertTemplateUsed(response, 'treemap/plot_detail_infowindow.html')
        self.assertIs(type(response.context['tree']), Tree)
        self.assertIs(type(response.context['plot']), Plot)
        self.assertEqual(response.context['tree'].id, self.p2_tree.current_tree().id)
        self.assertEqual(response.context['plot'].id, self.p2_tree.id)


    def test_get_choice_values(self):

        tree_url = ('/trees/%i/edit/choices/' % self.p2_tree.current_tree().id) + '%s/'
        plot_url = ('/plots/%i/edit/choices/' % self.p2_tree.id) + '%s/'

        response = self.client.get(tree_url % 'conditions')
        choices = loads(response.content)
        self.assertEquals(CHOICES['conditions'][0][1], choices[CHOICES['conditions'][0][0]] )
        response = self.client.get(tree_url % 'canopy_conditions')
        choices = loads(response.content)
        self.assertEquals(CHOICES['canopy_conditions'][0][1], choices[CHOICES['canopy_conditions'][0][0]] )
        response = self.client.get(tree_url % 'actions')
        choices = loads(response.content)
        self.assertEquals(CHOICES['actions'][0][1], choices[CHOICES['actions'][0][0]] )

        response = self.client.get(plot_url % 'sidewalks')
        choices = loads(response.content)
        self.assertEquals(CHOICES['sidewalks'][0][1], choices[CHOICES['sidewalks'][0][0]] )
        response = self.client.get(plot_url % 'powerlines')
        choices = loads(response.content)
        self.assertEquals(CHOICES['powerlines'][0][1], choices[CHOICES['powerlines'][0][0]] )


##################################################################
# stewardship tests
#

    def test_add_and_remove_stewardship_activities(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.post("/trees/%s/stewardship/" % self.p2_tree.current_tree().pk, { "activity": 1, "performed_date": "01/01/2012" })
        response_dict = loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dict["success"], True)

        response = c.post("/plots/%s/stewardship/" % self.p2_tree.pk, { "activity": 1, "performed_date": "01/01/2012" })
        response_dict = loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dict["success"], True)

        p = Plot.objects.get(pk=self.p2_tree.pk)
        t = p.current_tree()
        self.assertEqual(p.plotstewardship_set.count(), 1)
        self.assertEqual(t.treestewardship_set.count(), 1)

        plot_activities = PlotStewardship.objects.filter(plot=p)
        tree_activities = TreeStewardship.objects.filter(tree=t)

        response = c.get("/trees/%s/stewardship/%s/delete/" % (t.pk, tree_activities[0].pk))
        self.assertEqual(response.status_code, 200)

        response = c.get("/plots/%s/stewardship/%s/delete/" % (p.pk, plot_activities[0].pk))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(p.plotstewardship_set.count(), 0)
        self.assertEqual(t.treestewardship_set.count(), 0)

    def test_plot_delete(self):
        c = self.client
        c.login(username='jim',password='jim')

        plot_id = self.p2_tree.pk
        tree_id = self.p2_tree.current_tree().pk

        response = c.get("/plots/%d/delete/" % plot_id)
        self.assertEqual(200, response.status_code, "Expected 200 status code after delete")
        response_dict = loads(response.content)
        self.assertTrue('success' in response_dict, 'Expected a json object response with a "success" key')
        self.assertTrue(response_dict['success'], 'Expected a json object response with a "success" key set to True')

        plot = Plot.objects.get(pk=plot_id)
        tree = Tree.objects.get(pk=tree_id)

        self.assertFalse(plot.present, 'Expected "present" to be False on a deleted plot')
        for audit_trail_record in plot.history.all():
            self.assertFalse(audit_trail_record.present, 'Expected "present" to be False for all audit trail records for a deleted plot')

        self.assertFalse(tree.present, 'Expected "present" to be False on tree associated with a deleted plot')
        for audit_trail_record in tree.history.all():
            self.assertFalse(audit_trail_record.present, 'Expected "present" to be False for all audit trail records for tree associated with a deleted plot')

    def test_tree_delete(self):
        c = self.client
        c.login(username='jim',password='jim')

        plot_id = self.p2_tree.pk
        tree_id = self.p2_tree.current_tree().pk

        response = c.get("/trees/%d/delete/" % tree_id)
        self.assertEqual(200, response.status_code, "Expected 200 status code after delete")
        response_dict = loads(response.content)
        self.assertTrue('success' in response_dict, 'Expected a json object response with a "success" key')
        self.assertTrue(response_dict['success'], 'Expected a json object response with a "success" key set to True')

        plot = Plot.objects.get(pk=plot_id)
        tree = Tree.objects.get(pk=tree_id)

        self.assertTrue(plot.present, 'Expected "plot.present" to be True after deleting a tree from a plot')
        for audit_trail_record in plot.history.all():
            self.assertTrue(audit_trail_record.present, 'Expected "plot.present" to be True for all plot audit trail records after deleting the tree from the plot')

        self.assertFalse(tree.present, 'Expected "present" to be False on a deleted tree')
        for audit_trail_record in tree.history.all():
            self.assertFalse(audit_trail_record.present, 'Expected "present" to be False for all audit trail records for a deleted tree')


##################################################################
# Management page tests
#

    def test_watch_list(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.post('/trees/watch/')
        self.assertTemplateUsed(response, 'treemap/watch_list.html')

    def test_user_rep_list(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.get('/users/activity/')
        self.assertTemplateUsed(response, 'treemap/rep_changes.html')

    def test_comments_list(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.get('/comments/all/')
        self.assertTemplateUsed(response, 'comments/edit.html')

    def test_flagged_comments_list(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.get('/comments/moderate/')
        self.assertTemplateUsed(response, 'comments/edit_flagged.html')

    def test_images_list(self):
        c = self.client
        c.login(username='jim',password='jim')

        response = c.get('/images/')
        self.assertTemplateUsed(response, 'treemap/images.html')

class ExportModuleTests(TestCase):
    def setUp(self):
        self.raw_condition_query = \
            'SELECT * FROM "treemap_treeresource" '\
            'WHERE "treemap_treeresource"."tree_id" IN '\
            '(SELECT U0."id" FROM "treemap_tree" U0 '\
            'WHERE  AND U0."condition" IN (3, 5, 7))'

        self.correct_condition_query = \
            'SELECT * FROM "treemap_treeresource" '\
            'WHERE "treemap_treeresource"."tree_id" IN '\
            '(SELECT U0."id" FROM "treemap_tree" U0 '\
            'WHERE  AND U0."condition" IN (\'3\', \'5\', \'7\'))'

        self.raw_condition_characteristic_query = \
            'SELECT * FROM "treemap_tree" '\
            'WHERE ("treemap_tree"."condition" IN (2, 3, 4, 5, 6, 7) AND '\
           '"treemap_tree"."species_id" IN '\
            '(SELECT U0."id" FROM "treemap_species" U0 WHERE U0."native_status" = True ))'

        self.correct_condition_characteristic_query = \
            'SELECT * FROM "treemap_tree" '\
            'WHERE ("treemap_tree"."condition" IN (\'2\', \'3\', \'4\', \'5\', \'6\', \'7\') AND '\
           '"treemap_tree"."species_id" IN '\
            '(SELECT U0."id" FROM "treemap_species" U0 WHERE U0."native_status" = \'True\' ))'


    def test_multiple_fields_query(self):

        condition_characteristic_query = sanitize_raw_sql(self.raw_condition_characteristic_query)

        self.assertEqual(condition_characteristic_query,
                         self.correct_condition_characteristic_query)

    def test_condition_query(self):
        condition_query = sanitize_raw_sql(self.raw_condition_query)

        self.assertEqual(condition_query, self.correct_condition_query)
