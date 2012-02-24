"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User, UserManager, Permission as P
from django.contrib.gis.geos import Point
from django.test import TestCase
from simplejson import loads

from django.conf import settings
from test_util import setupTreemapEnv, teardownTreemapEnv, mkPlot, mkTree
from treemap.models import Choices, Species

API_PFX = "/api/v0.1"

class Version(TestCase):
    def setUp(self):
        settings.GEOSERVER_GEO_LAYER = ""
        settings.GEOSERVER_GEO_STYLE = ""
        settings.GEOSERVER_URL = ""

    def test_version(self):
        settings.OTM_VERSION = "1.2.3"
        settings.API_VERSION = "0.1"

        ret = self.client.get("%s/version" % API_PFX)

        self.assertEqual(ret.status_code, 200)
        json = loads(ret.content)

        self.assertEqual(json["otm_version"], settings.OTM_VERSION)
        self.assertEqual(json["api_version"], settings.API_VERSION)

class PlotListing(TestCase):
    def setUp(self):
        settings.GEOSERVER_GEO_LAYER = ""
        settings.GEOSERVER_GEO_STYLE = ""
        settings.GEOSERVER_URL = ""

        setupTreemapEnv()

        self.u = User.objects.get(username="jim")

    def tearDown(self):
        teardownTreemapEnv()
        
    def test_basic_data(self):
        p = mkPlot(self.u)
        p.width = 22
        p.length = 44
        p.present = True
        p.geometry = Point(55,56)
        p.geometry.srid = 4326
        p.readonly = False
        p.save()

        info = self.client.get("%s/plots" % API_PFX)

        self.assertEqual(info.status_code, 200)
        
        json = loads(info.content)

        self.assertEqual(len(json), 1)
        record = json[0]

        self.assertEqual(record["id"], p.pk)
        self.assertEqual(record["width"], 22)
        self.assertEqual(record["length"], 44)
        self.assertEqual(record["readonly"], False)
        self.assertEqual(record["geometry"]["srid"], 4326)
        self.assertEqual(record["geometry"]["lat"], 56)
        self.assertEqual(record["geometry"]["lng"], 55)
        self.assertEqual(record.get("tree"), None)

    def test_tree_data(self):
        p = mkPlot(self.u)
        t = mkTree(self.u, plot=p)

        t.species = None
        t.dbh = None
        t.present = True
        t.save()

        info = self.client.get("%s/plots" % API_PFX)

        self.assertEqual(info.status_code, 200)
        
        json = loads(info.content)

        self.assertEqual(len(json), 1)
        record = json[0]

        self.assertEqual(record["tree"]["id"], t.pk)

        t.species = Species.objects.all()[0]
        t.dbh = 11.2
        t.save()

        info = self.client.get("%s/plots" % API_PFX)

        self.assertEqual(info.status_code, 200)
        
        json = loads(info.content)

        self.assertEqual(len(json), 1)
        record = json[0]

        self.assertEqual(record["tree"]["species"], t.species.pk)
        self.assertEqual(record["tree"]["dbh"], t.dbh)
        self.assertEqual(record["tree"]["id"], t.pk)

    def test_paging(self):
        p0 = mkPlot(self.u)
        p0.present = False
        p0.save()

        p1 = mkPlot(self.u)
        p2 = mkPlot(self.u)
        p3 = mkPlot(self.u)

        r = self.client.get("%s/plots?offset=0&size=2" % API_PFX)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p1.pk, p2.pk]))


        r = self.client.get("%s/plots?offset=1&size=2" % API_PFX)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p2.pk, p3.pk]))


        r = self.client.get("%s/plots?offset=2&size=2" % API_PFX)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p3.pk]))


        r = self.client.get("%s/plots?offset=3&size=2" % API_PFX)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set())

        r = self.client.get("%s/plots?offset=0&size=5" % API_PFX)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p1.pk, p2.pk, p3.pk]))

class Locations(TestCase):
    def setUp(self):
        settings.GEOSERVER_GEO_LAYER = ""
        settings.GEOSERVER_GEO_STYLE = ""
        settings.GEOSERVER_URL = ""

        setupTreemapEnv()

        self.user = User.objects.get(username="jim")

    def test_locations_plots_endpoint(self):
        response = self.client.get("%s/locations/0,0/plots" % API_PFX)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_max_plots_param_must_be_a_number(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=foo" % API_PFX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')

    def test_locations_plots_endpoint_max_plots_param_cannot_be_greater_than_500(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=501" % API_PFX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')
        response = self.client.get("%s/locations/0,0/plots?max_plots=500" % API_PFX)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_max_plots_param_cannot_be_less_than_1(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=0" % API_PFX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')
        response = self.client.get("%s/locations/0,0/plots?max_plots=1" % API_PFX)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_distance_param_must_be_a_number(self):
        response = self.client.get("%s/locations/0,0/plots?distance=foo" % API_PFX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The distance parameter must be a number')
        response = self.client.get("%s/locations/0,0/plots?distance=42" % API_PFX)
        self.assertEqual(response.status_code, 200)

    def test_plots(self):
        plot = mkPlot(self.user)
        plot.present = True
        plot.save()

        response = self.client.get("%s/locations/%s,%s/plots" % (API_PFX, plot.geometry.x, plot.geometry.y))

        self.assertEqual(response.status_code, 200)
        json = loads(response.content)