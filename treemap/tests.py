import os
from django import forms
from django.test import TestCase
from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.contrib.auth.models import User, UserManager, Permission as P

from treemap.models import Neighborhood, ZipCode
from treemap.models import Plot, ImportEvent, Species, Tree
from treemap.models import BenefitValues, Resource, AggregateNeighborhood
from treemap.views import *

from profiles.models import UserProfile
from django_reputation.models import Reputation, ReputationAction

from simplejson import loads
from datetime import datetime, date
from time import mktime

from test_util import set_auto_now

#        from IPython.Debugger import Tracer; debug_here = Tracer(); debug_here()


import django.shortcuts

class ViewTests(TestCase):

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

            if hasattr(args[1], 'dicts'):
                hr.request_context = args[1].dicts

            return hr

        django.shortcuts.render_to_response = local_render_to_response
    
        ######
        # Set up benefit values
        ######
        bv = BenefitValues(co2=0.02, pm10=9.41, area="InlandValleys",
                           electricity=0.1166,voc=4.69,ozone=5.0032,natural_gas=1.25278,
                           nox=12.79,stormwater=0.0078,sox=3.72,bvoc=4.96)

        bv.save()
        self.bv = bv


        dbh = "[1.0, 2.0, 3.0]"
        rsrc = Resource(meta_species="BDM_OTHER", electricity_dbh=dbh, co2_avoided_dbh=dbh,
                        aq_pm10_dep_dbh=dbh, region="Sim City", aq_voc_avoided_dbh=dbh,
                        aq_pm10_avoided_dbh=dbh, aq_ozone_dep_dbh=dbh, aq_nox_avoided_dbh=dbh,
                        co2_storage_dbh=dbh,aq_sox_avoided_dbh=dbh, aq_sox_dep_dbh=dbh,
                        bvoc_dbh=dbh, co2_sequestered_dbh=dbh, aq_nox_dep_dbh=dbh,
                        hydro_interception_dbh=dbh, natural_gas_dbh=dbh)
        rsrc.save()
        self.rsrc = rsrc

        ######
        # Users
        ######
        u = User.objects.filter(username="jim")
            
        if u:
            u = u[0]
        else:
            u = User.objects.create_user("jim","jim@test.org","jim")
            u.is_staff = True
            u.is_superuser = True
            u.save()
            up = UserProfile(user=u)
            u.reputation = Reputation(user=u)
            u.reputation.save()

        self.u = u

        ra1 = ReputationAction(name="add tree", description="User added a tree")
        ra1.save()
        

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

        agn1 = AggregateNeighborhood(
            annual_stormwater_management=0.0,
            annual_electricity_conserved=0.0,
            annual_energy_conserved=0.0,
            annual_natural_gas_conserved=0.0,
            annual_air_quality_improvement=0.0,
            annual_co2_sequestered=0.0,
            annual_co2_avoided=0.0,
            annual_co2_reduced=0.0,
            total_co2_stored=0.0,
            annual_ozone=0.0,
            annual_nox=0.0,
            annual_pm10=0.0,
            annual_sox=0.0,
            annual_voc=0.0,
            annual_bvoc=0.0,
            total_trees=0,
            total_plots=0,
            location = n1)

        agn2 = AggregateNeighborhood(
            annual_stormwater_management=0.0,
            annual_electricity_conserved=0.0,
            annual_energy_conserved=0.0,
            annual_natural_gas_conserved=0.0,
            annual_air_quality_improvement=0.0,
            annual_co2_sequestered=0.0,
            annual_co2_avoided=0.0,
            annual_co2_reduced=0.0,
            total_co2_stored=0.0,
            annual_ozone=0.0,
            annual_nox=0.0,
            annual_pm10=0.0,
            annual_sox=0.0,
            annual_voc=0.0,
            annual_bvoc=0.0,
            total_trees=0,
            total_plots=0,
            location = n2)

        agn1.save()
        agn2.save()

        self.agn1 = agn1
        self.agn2 = agn2

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
        self.agn1.delete()
        self.agn2.delete()

        self.bv.delete()
        self.rsrc.delete()

        self.n1.delete()
        self.n2.delete()

        self.p1_no_tree.delete()

        self.t1.delete()
        self.p2_tree.delete()

        self.t2.delete()
        self.p3_tree_species1.delete()

        self.t3.delete()
        self.p4_tree_species2.delete()

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
        

#############################################
#  New Plot Tests

    def test_add_plot(self):
        self.client.login(username='jim',password='jim')
        form = {}
        form['target']="edit"
        ##################################################################
        # Test required information: 
        #     lat,lon,entered address and geocoded address
        
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')
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
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)

        response = self.client.get('/trees/new/%i/' % self.u.id)
        self.assertNotEqual(len(response.context['plots']), 0)
        new_plot = response.context['plots'][0]        
        
        self.assertTrue(new_plot.geocoded_address, form['geocode_address'])
    
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
        # plot width < 12
        form['plot_width_in'] = "20"
        self.assertTemplateUsed(self.client.post("/trees/add/", form), 'treemap/tree_add.html')  
        form['plot_width_in'] = ""
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
    
        response = self.client.post("/trees/add/", form)
        self.assertRedirects(response, '/trees/new/%i/' % self.u.id)
        
        response = self.client.get('/trees/new/%i/' % self.u.id)
        new_plot = response.context['plots'][0]   
        self.assertAlmostEqual(new_plot.width, 5.0)
        self.assertAlmostEqual(new_plot.length, 6.5)
        self.assertEqual(new_plot.current_tree(), None)
        self.assertEqual(new_plot.zipcode, self.z1)
        self.assert_point_in_nhood(new_plot.geometry, self.n1)

        new_plot = None
        
        ##################################################################
        # Test tree creation: 
        #     Info in the rest of the fields creates a tree object as well as a plot

        form['species_id'] = "s1"
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
        
        response = self.client.get('/trees/new/%i/' % self.u.id)
        new_plot = response.context['plots'][0]   
        new_tree = new_plot.current_tree()
        self.assertNotEqual(new_tree, None)
        self.assertEqual(new_tree.species.genus, "testus1")
        self.assertAlmostEqual(new_tree.dbh, 2/math.pi)
        self.assertEqual(new_tree.plot, new_plot)
        


