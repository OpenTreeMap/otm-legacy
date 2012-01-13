import os
from django import forms
from django.utils import unittest
from django.test.client import Client
from django.contrib.gis.geos import MultiPolygon, Polygon, Point
from django.contrib.auth.models import User, UserManager

from treemap.models import Neighborhood, ZipCode
from treemap.models import Plot, ImportEvent, Species, Tree
from treemap.forms import TreeAddForm

from profiles.models import UserProfile
from django_reputation.models import Reputation

from simplejson import loads

#        from IPython.Debugger import Tracer; debug_here = Tracer(); debug_here()

class ViewTests(unittest.TestCase):

    def setUp(self):
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

        p1_no_tree = Plot(geometry=Point(50,50), last_updated_by=u, import_event=ie,present=True)
        p1_no_tree.save()

        p2_tree = Plot(geometry=Point(51,51), last_updated_by=u, import_event=ie,present=True)
        p2_tree.save()

        p3_tree_species1 = Plot(geometry=Point(50,100), last_updated_by=u, import_event=ie,present=True)
        p3_tree_species1.save()

        p4_tree_species2 = Plot(geometry=Point(50,150), last_updated_by=u, import_event=ie,present=True)
        p4_tree_species2.save()

        t1 = Tree(plot=p2_tree, species=None, last_updated_by=u, import_event=ie)
        t1.save()
        
        t2 = Tree(plot=p3_tree_species1, species=s1, last_updated_by=u, import_event=ie)
        t2.save()

        t3 = Tree(plot=p4_tree_species2, species=s2, last_updated_by=u, import_event=ie)
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


#############################################
#  New Plot Tests

    def test_add_plot(self):
        request = self.factory.post('/trees/add/')
        form = {}
        ##################################################################
        # Test required information: 
        #     lat,lon,entered address and geocoded address
        
        self.assertRaises(forms.ValidationError, form.save(request))
        form.lat=50
        self.assertRaises(forms.ValidationError, form.save(request))
        form.lon=50
        self.assertRaises(forms.ValidationError, form.save(request))
        form.edit_address_street = "100 N Broad"
        self.assertRaises(forms.ValidationError, form.save(request))
        form.edit_address_street = None
        form.geocoded_address = "100 N Broad St"
        self.assertRaises(forms.ValidationError, form.save(request))
        form.edit_address_street = "100 N Broad"
        new_plot = form.save(request)
        self.assertNotEqual(new_plot, None)
        new_plot.delete()
        new_plot = None

        ##################################################################
        # Test plot-only creation: 
        #     Info in these fields creates a plot object, and does not
        #     create a tree object
        
        form.edit_address_city = "Philadelphia"
        form.edit_address_zip = "19107"
        form.plot_width = "50"  
        form.plot_width_in = "0"  
        form.plot_length = "6"
        form.plot_length_in = "6"
        form.plot_type = "Open"  
        form.powerline_conflict_potential = 1  
        form.sidewalk_damage = 1  

        # plot width < 15
        self.assertRaises(forms.ValidationError, form.save(request))        
        form.plot_width = "5"
        # plot width < 12
        form.plot_width_in = "20"
        self.assertRaises(forms.ValidationError, form.save(request))   
        form.plot_width_in = "0"
        # plot type in type list
        self.plot_type = "Blargh"
        self.assertRaises(forms.ValidationError, form.save(request))   
        self.plot_type = "Open"
        # powerlines = 1, 2, or 3
        self.powerline_conflict_potential = 15
        self.assertRaises(forms.ValidationError, form.save(request))   
        self.powerline_conflict_potential = 1
        # powerlines = 1, 2, or 3
        self.sidewalk_damage = 15
        self.assertRaises(forms.ValidationError, form.save(request))   
        self.sidewalk_damage = 1
    
        new_plot = form.save()
        self.assertAlmostEqual(new_plot.width, 5.0)
        self.assertAlmostEqual(new_plot.length, 6.5)
        self.assertEqual(new_plot.current_tree(), None)
        self.assertEqual(new_plot.zipcode, z1)
        self.assert_point_in_nhood(new_plot.geometry, n1)

        new_plot.delete()
        new_plot = None
        
        ##################################################################
        # Test tree creation: 
        #     Info in the rest of the fields creates a tree object as well as a plot

        form.species_id = "s1"
        form.height = 50  
        form.canopy_height = 40  
        form.dbh = 2 
        form.dbh_type = "circumference"
        form.condition = "Good"  
        form.canopy_condition = "Full - No Gaps"
        
        # height <= 300
        form.height = 500
        self.assertRaises(forms.ValidationError, form.save(request)) 
        form.height = 60 
        # canopy height <= 300
        form.canopy_height = 550
        self.assertRaises(forms.ValidationError, form.save(request))  
        # canopy height <= height
        form.canopy_height = 80
        self.assertRaises(forms.ValidationError, form.save(request))  
        form.canopy_height = 40
        # condition in list
        form.condition = "Blah"
        self.assertRaises(forms.ValidationError, form.save(request))  
        form.condition = "Good"
        # canopy condition in list
        form.canopy_condition = "Blah"
        self.assertRaises(forms.ValidationError, form.save(request))  
        form.canopy_condition = "Full - No Gaps"

        new_plot = form.save()
        new_tree = new_plot.current_tree()
        self.assertNotEqual(new_tree, None)
        self.assertEqual(new_tree.species, s1)
        self.assertAlmostEqual(new_tree.dbh, 2/math.pi)
        self.assertEqual(new_tree.plot, new_plot)
        


