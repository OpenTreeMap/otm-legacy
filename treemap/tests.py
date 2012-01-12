import os
from django.utils import unittest
from django.test.client import Client
from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.contrib.auth.models import User, UserManager

from treemap.models import Neighborhood, ZipCode
from treemap.models import Plot, ImportEvent, Species, Tree

from profiles.models import UserProfile
from django_reputation.models import Reputation

from simplejson import loads
from datetime import datetime, date
from time import mktime

from test_util import set_auto_now

#        from IPython.Debugger import Tracer; debug_here = Tracer(); debug_here()


import django.shortcuts

class ViewTests(unittest.TestCase):

    def setUp(self):
        ######
        # Request/Render mock
        ######
        def local_render_to_response(*args, **kwargs):
            from django.template import loader, RequestContext
            from django.http import HttpResponse

            httpresponse_kwargs = {'mimetype': kwargs.pop('mimetype', None)}
            hr = HttpResponse(
                loader.render_to_string(*args, **kwargs), **httpresponse_kwargs)

            hr.request_context = args[1].dicts

            return hr

        django.shortcuts.render_to_response = local_render_to_response


        ######
        # Users
        ######
        u = User.objects.filter(username="jim").all()

        if u:
            u = u[0]
        else:
            u = User.objects.create_user("jim","jim@test.org","jim")
            up = UserProfile(user=u)
            u.reputation = Reputation(user=u)
            u.reputation.save()
            
            u.save()

        self.u = u

        #######
        # Setup geometries -> Two stacked 100x100 squares
        #######
        n1geom = MultiPolygon(Polygon(((0,0),(100,0),(100,100),(0,100),(0,0))))
        n2geom = MultiPolygon(Polygon(((0,101),(101,101),(101,200),(0,200),(0,101))))

        n1 = Neighborhood(name="n1", region_id=2, city="c1", state="PA", county="PAC", geometry=n1geom)
        n2 = Neighborhood(name="n2", region_id=2, city="c2", state="NY", county="NYC", geometry=n2geom)

        n1.save()
        n2.save()

        z1geom = MultiPolygon(Polygon(((0,0),(100,0),(100,100),(0,100),(0,0))))
        z2geom = MultiPolygon(Polygon(((0,100),(100,100),(100,200),(0,200),(0,100))))

        z1 = ZipCode(zip="19107",geometry=z1geom)
        z2 = ZipCode(zip="10001",geometry=z2geom)

        z1.save()
        z2.save()

        self.z1 = z1
        self.z2 = z2
        self.n1 = n1
        self.n2 = n2

        ######
        # And we could use a few species...
        ######
        s1 = Species(symbol="s1",genus="testus1",species="specieius1")
        s2 = Species(symbol="s2",genus="testus2",species="specieius2")
        
        s1.save()
        s2.save()

        self.s1 = s1
        self.s2 = s2

        #######
        # Create some basic plots
        #######
        ie = ImportEvent(file_name='site_add')
        ie.save()

        self.ie = ie

        p1_no_tree = Plot(geometry=Point(50,50), last_updated_by=u, import_event=ie,present=True)
        p1_no_tree.save()

        p2_tree = Plot(geometry=Point(51,51), last_updated_by=u, import_event=ie,present=True)
        p2_tree.save()

        p3_tree_species1 = Plot(geometry=Point(50,100), last_updated_by=u, import_event=ie,present=True)
        p3_tree_species1.save()

        p4_tree_species2 = Plot(geometry=Point(50,150), last_updated_by=u, import_event=ie,present=True)
        p4_tree_species2.save()

        t1 = Tree(plot=p2_tree, species=None, last_updated_by=u, import_event=ie)
        t1.present = True
        t1.save()
        
        t2 = Tree(plot=p3_tree_species1, species=s1, last_updated_by=u, import_event=ie)
        t2.present = True
        t2.save()

        t3 = Tree(plot=p4_tree_species2, species=s2, last_updated_by=u, import_event=ie)
        t3.present = True
        t3.save()

        self.p1_no_tree = p1_no_tree
        self.p2_tree = p2_tree
        self.p3_tree_species1 = p3_tree_species1;
        self.p4_tree_species2 = p4_tree_species2;

        self.plots = [p1_no_tree, p2_tree, p3_tree_species1, p4_tree_species2]

        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        
    def tearDown(self):
        self.p1_no_tree.delete()

        self.t1.delete()
        self.p2_tree.delete()

        self.t2.delete()
        self.p3_tree_species1.delete()

        self.t3.delete()
        self.p4_tree_species2.delete()

    def test_plot_location_search_error_cases(self):
        """ Test error cases for plot location search """
        client = Client()

        # The following errors should all be 400 -> Malformed Request

        # Error case -> Missing get data
        # Requires lat,lon or bbox
        response = client.get("/plots/location/")
        self.assertEqual(response.status_code, 400)
        
        response = client.get("/plots/location/?lat=-77")
        self.assertEqual(response.status_code, 400)

        response = client.get("/plots/location/?lon=-32")
        self.assertEqual(response.status_code, 400)

    def geojson_ft2id(self,geojson):
        if geojson and "features" in geojson:
            return set([int(ft["properties"]["id"]) for ft in geojson["features"]])
        else:
            return set()

    def assert_geojson_has_ids(self, geojson, ids):
        return self.assertEqual(self.geojson_ft2id(geojson), ids)

    def test_plot_location_search_pt(self):
        """ Test searching for plot by pt """
        client = Client()

        reqstr = "/plots/location/?lat=%s&lon=%s&distance=%s&max_plots=%s"

        ##################################################################
        # Limit max plots to 1 - expect to get only 1 plot back
        response = client.get(reqstr % (50,50,1000,1))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p1_no_tree.pk]))

        ##################################################################
        # Limit distance to 5, expect to get only two (50,50) and (51,51) back
        response = client.get(reqstr % (50,50,5,100))
        geojson = loads(response.content)
        
        exp = set([self.p1_no_tree.pk, self.p2_tree.pk])

        self.assert_geojson_has_ids(geojson, exp)
        
        ##################################################################
        # Effective unlimited distance should return all plots
        response = client.get(reqstr % (50,50,10000,100))
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

        response = client.get(reqstr % (self.s1.pk))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p3_tree_species1.pk]))

        response = client.get(reqstr % (self.s2.pk))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([self.p4_tree_species2.pk]))

        ##################################################################
        # -> If a species is specified:
        #      AND results in NO distance matches
        #      THEN return the original results, unfiltered
        #
        
        response = client.get(reqstr % (1000000))
        geojson = loads(response.content)

        self.assert_geojson_has_ids(geojson, set([p.pk for p in self.plots]))

    def test_result_map(self):
        ##################################################################
        # Test main result map page
        # Note -> This page does not depend at all on the request
        #
        
        p1 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie,present=True, width=100, length=100)
        p2 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=90, length=110)

        p1.save()
        p2.save()

        # For max/min plot size
        p3 = Plot(geometry=Point(50,50), last_updated_by=self.u, import_event=self.ie,present=True, width=80, length=120)
        p4 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=70, length=130)
        p5 = Plot(geometry=Point(60,50), last_updated_by=self.u, import_event=self.ie,present=True, width=60, length=70)

        p3.save()
        p4.save()
        p5.save()

        t3 = Tree(plot=p3, species=None, region="blah", last_updated_by=self.u, import_event=self.ie,present=True)
        t3.save()

        t4 = Tree(plot=p4, species=None, region="blah", last_updated_by=self.u, import_event=self.ie,present=True)
        t4.save()

        t5 = Tree(plot=p5, species=None, region="blah", last_updated_by=self.u, import_event=self.ie,present=True)
        t5.save()

        t1 = Tree(plot=p1, species=None, region="blah", last_updated_by=self.u, import_event=self.ie)
        t1.present = True
        
        current_year = datetime.now().year    
        t1.date_planted = date(1999,9,9)

        t2 = Tree(plot=p2, species=None, region="blah", last_updated_by=self.u, import_event=self.ie)
        t1.present = True

        t1.save()
        t2.save()

        set_auto_now(t1, "last_updated", False)
        t1.last_updated = date(1999,9,9)
        t1.save()
        
        response = Client().get("/map/")
        req = response.request_context[0]

        # t1 and t2 should be in the latest trees
        exp = set([t4.pk, t5.pk])
        got = set([t.pk for t in req['latest_trees']])

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
        

