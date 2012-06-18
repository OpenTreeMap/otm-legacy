"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from StringIO import StringIO

from django.contrib.auth.models import User, UserManager, Permission as P
from django.contrib.gis.geos import Point
from django.test import TestCase
from django_reputation.models import UserReputationAction
from simplejson import loads, dumps

from django.conf import settings
from urlparse import urlparse
import urllib
from test_utils import setupTreemapEnv, teardownTreemapEnv, mkPlot, mkTree
from treemap.models import Choices, Species, Plot, Tree, Pending, TreePending, PlotPending

from api.models import APIKey, APILog
from api.views import InvalidAPIKeyException

import struct
import base64

API_PFX = "/api/v0.1"

def create_signer_dict(user):
    key = APIKey(user=user,key="TESTING",enabled=True,comment="")
    key.save()

    return { "HTTP_X_API_KEY": key.key }

def send_json_body(url, body_object, client, method, sign_dict=None):
    """
    Serialize a list or dictionary to JSON then send it to an endpoint.
    The "post" method exposed by the Django test client assumes that you
    are posting form data, so you need to manually setup the parameters
    to override that default functionality.
    """
    def _get_path(parsed_url):
        """
        Taken from a class method in the Django test client
        """
        # If there are parameters, add them
        if parsed_url[3]:
            return urllib.unquote(parsed_url[2] + ";" + parsed_url[3])
        else:
            return urllib.unquote(parsed_url[2])

    body_string = dumps(body_object)
    body_stream = StringIO(body_string)
    parsed_url = urlparse(url)
    client_params = {
        'CONTENT_LENGTH': len(body_string),
        'CONTENT_TYPE': 'application/json',
        'PATH_INFO': _get_path(parsed_url),
        'QUERY_STRING': parsed_url[4],
        'REQUEST_METHOD': method,
        'wsgi.input': body_stream,
    }

    if sign_dict is not None:
        client_params.update(sign_dict)

    return client.post(url, **client_params)

def post_json(url, body_object, client, sign_dict=None):
    """
    Serialize a list or dictionary to JSON then POST it to an endpoint.
    The "post" method exposed by the Django test client assumes that you
    are posting form data, so you need to manually setup the parameters
    to override that default functionality.
    """
    return send_json_body(url, body_object, client, 'POST', sign_dict)

def put_json(url, body_object, client, sign_dict=None):
    return send_json_body(url, body_object, client, 'PUT', sign_dict)

class Signing(TestCase):
    def setUp(self):
        settings.OTM_VERSION = "1.2.3"
        settings.API_VERSION = "0.1"

        setupTreemapEnv()

        self.u = User.objects.get(username="jim")

    def test_unsigned_will_fail(self):
        self.assertRaises(InvalidAPIKeyException, self.client.get,"%s/version" % API_PFX)

    def test_signed_header(self):
        key = APIKey(user=self.u,key="TESTING",enabled=True,comment="")
        key.save()
        
        ret = self.client.get("%s/version" % API_PFX, **{ "HTTP_X_API_KEY": key.key })
        self.assertEqual(ret.status_code, 200)

    def test_url_param(self):
        key = APIKey(user=self.u,key="TESTING",enabled=True,comment="")
        key.save()
        
        ret = self.client.get("%s/version?apikey=%s" % (API_PFX,key.key))
        self.assertEqual(ret.status_code, 200)

    def test_disabled_keys_dont_work(self):
        key = APIKey(user=self.u,key="TESTING",enabled=False,comment="")
        key.save()

        self.assertRaises(InvalidAPIKeyException, self.client.get, "%s/version" % API_PFX, **{ "X-API-Key": key.key })


    def tearDown(self):
        teardownTreemapEnv()


class Authentication(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")
        self.u.set_password("password")
        self.u.save()

        amy = User.objects.get(username="amy")
        amy.set_password("password")
        amy.save()

        self.sign = create_signer_dict(self.u)

    def test_401(self):
        ret = self.client.get("%s/login" % API_PFX, **self.sign)
        self.assertEqual(ret.status_code, 401)
        

    def test_ok(self):
        auth = base64.b64encode("jim:password")
        withauth = dict(self.sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % auth)])

        ret = self.client.get("%s/login" % API_PFX, **withauth)
        self.assertEqual(ret.status_code, 200)

    def test_bad_cred(self):
        auth = base64.b64encode("jim:passwordz")
        withauth = dict(self.sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % auth)])

        ret = self.client.get("%s/login" % API_PFX, **withauth)
        self.assertEqual(ret.status_code, 401)

    def test_includes_permissions(self):
        amy = User.objects.get(username="amy")
        self.assertEqual(len(amy.user_permissions.all()), 0, 'Expected the test setUp to create user "amy" with no permissions')

        amy.user_permissions.add(P.objects.get(codename="delete_tree"))
        amy.save()
        amys_perm_count = len(amy.user_permissions.all())

        auth = base64.b64encode("amy:password")
        withauth = dict(self.sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % auth)])

        ret = self.client.get("%s/login" % API_PFX, **withauth)
        self.assertEqual(ret.status_code, 200, "Authentication failed so testing for permissions is blocked")
        self.assertIsNotNone(ret.content, "Response had no content so testing for permissions is blocked")
        content_dict = loads(ret.content)
        self.assertTrue('permissions' in content_dict, "The response did not contain a permissions attribute")
        self.assertEqual(amys_perm_count, len(content_dict['permissions']))
        self.assertTrue('treemap.delete_tree' in content_dict['permissions'], 'The "delete_tree" permission was not in the permissions list for the test user.')

    def tearDown(self):
        teardownTreemapEnv()

class Logging(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")
        self.sign = create_signer_dict(self.u)

    def test_log_request(self):
        ret = self.client.get("%s/version?rvar=4,rvar2=5" % API_PFX, **self.sign)
        self.assertEqual(ret.status_code, 200)
        
        logs = APILog.objects.all()

        self.assertTrue(logs is not None and len(logs) == 1)

        key = APIKey.objects.get(user=self.u)
        log = logs[0]

        self.assertEqual(log.apikey,key)
        self.assertEqual(log.url, "%s/version?rvar=4,rvar2=5" % API_PFX)
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.requestvars, "rvar=4,rvar2=5")

    def tearDown(self):
        teardownTreemapEnv()

class Version(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")
        self.sign = create_signer_dict(self.u)

    def test_version(self):
        settings.OTM_VERSION = "1.2.3"
        settings.API_VERSION = "0.1"

        ret = self.client.get("%s/version" % API_PFX, **self.sign)

        self.assertEqual(ret.status_code, 200)
        json = loads(ret.content)

        self.assertEqual(json["otm_version"], settings.OTM_VERSION)
        self.assertEqual(json["api_version"], settings.API_VERSION)
        
        def tearDown(self):
            tearDownTreemapEnv()

class TileRequest(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")

        self.sign = create_signer_dict(self.u)

    def tearDown(self):
        teardownTreemapEnv()
        
    def test_returns(self):
        p1 = mkPlot(self.u)
        p1.geometry = Point(-77,36)
        p1.save()

        p2 = mkPlot(self.u)
        p2.geometry = Point(-77.1,36.1)
        p2.save()

        #
        # Test #1 - Simple request
        # bbox(-78,35,-76,37) <--> bbox(-8682920,4163881,-8460281,4439106)
        #
        # Origin is bottom left
        #
        # Expected values:
        p1x = -77.0
        p1y = 36.0
        p1xM = -8571600.0
        p1yM = 4300621.0
        p2x = -77.1
        p2y = 36.1
        p2xM = -8582732.0
        p2yM = 4314389.0
        
        # Offset X values
        p1offsetx = p1xM - -8682920 #xmin
        p2offsetx = p2xM - -8682920 #xmin

        p1offsety = p1yM - 4163881.0 #ymin
        p2offsety = p2yM - 4163881.0 #ymin

        # Compute scale
        pixelsPerMeterX = 255.0 / (-8460281.0 - -8682920.0)
        pixelsPerMeterY = 255.0 / (4439106.0 - 4163881.0)

        # Computer origin offsets
        pixels1x = int(p1offsetx * pixelsPerMeterX + 0.5)
        pixels2x = int(p2offsetx * pixelsPerMeterX + 0.5)

        pixels1y = int(p1offsety * pixelsPerMeterY + 0.5)
        pixels2y = int(p2offsety * pixelsPerMeterY + 0.5)

        style = 0
        npts = 2

        # Format:
        # | File Header           | Section Header             | Pts                                        |
        # |0xA3A5EA00 | int: size | byte: style | short: # pts | 00 | byte:x1 | byte:y1 | byte:x2 | byte:y2 |
        testoutp = struct.pack("<IIBHxBBBB", 0xA3A5EA00, npts, style, npts, pixels2x, pixels2y, pixels1x, pixels1y)

        outp = self.client.get("%s/tiles?bbox=-78,35,-76,37" % API_PFX, **self.sign)

        self.assertEqual(testoutp, outp.content)
        

    def test_eats_same_point(self):
        x = 128 # these values come from the test_returns
        y = 127 # test case

        p1 = mkPlot(self.u)
        p1.geometry = Point(-77.0,36.0)
        p1.save()

        p2 = mkPlot(self.u)
        p2.geometry = Point(-77.0,36.0000001)
        p2.save()

        p3 = mkPlot(self.u)
        p3.geometry = Point(-76.99999,36)
        p3.save()

        p4 = mkPlot(self.u)
        p4.geometry = Point(-77.0,35.999999)
        p4.save()

        # These should all map to (x,y)->(128,127)
        npts = 1
        style = 0

        # Format:
        # | File Header           | Section Header             | Pts                                        |
        # |0xA3A5EA00 | int: size | byte: style | short: # pts | 00 | byte:x1 | byte:y1 | byte:x2 | byte:y2 |
        testoutp = struct.pack("<IIBHxBB", 0xA3A5EA00, npts, style, npts, x,y)
        
        outp = self.client.get("%s/tiles?bbox=-78,35,-76,37" % API_PFX, **self.sign)

        self.assertEqual(testoutp, outp.content)
        

class PlotListing(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.u = User.objects.get(username="jim")
        self.sign = create_signer_dict(self.u)

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

        info = self.client.get("%s/plots" % API_PFX, **self.sign)

        self.assertEqual(info.status_code, 200)
        
        json = loads(info.content)

        self.assertEqual(len(json), 1)
        record = json[0]

        self.assertEqual(record["id"], p.pk)
        self.assertEqual(record["plot_width"], 22)
        self.assertEqual(record["plot_length"], 44)
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

        info = self.client.get("%s/plots" % API_PFX, **self.sign)

        self.assertEqual(info.status_code, 200)
        
        json = loads(info.content)

        self.assertEqual(len(json), 1)
        record = json[0]

        self.assertEqual(record["tree"]["id"], t.pk)

        t.species = Species.objects.all()[0]
        t.dbh = 11.2
        t.save()

        info = self.client.get("%s/plots" % API_PFX, **self.sign)

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

        r = self.client.get("%s/plots?offset=0&size=2" % API_PFX, **self.sign)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p1.pk, p2.pk]))


        r = self.client.get("%s/plots?offset=1&size=2" % API_PFX, **self.sign)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p2.pk, p3.pk]))


        r = self.client.get("%s/plots?offset=2&size=2" % API_PFX, **self.sign)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p3.pk]))


        r = self.client.get("%s/plots?offset=3&size=2" % API_PFX, **self.sign)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set())

        r = self.client.get("%s/plots?offset=0&size=5" % API_PFX, **self.sign)

        rids = set([p["id"] for p in loads(r.content)])
        self.assertEqual(rids, set([p1.pk, p2.pk, p3.pk]))

class Locations(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.user = User.objects.get(username="jim")
        self.sign = create_signer_dict(self.user)

    def test_locations_plots_endpoint(self):
        response = self.client.get("%s/locations/0,0/plots" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_max_plots_param_must_be_a_number(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=foo" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')

    def test_locations_plots_endpoint_max_plots_param_cannot_be_greater_than_500(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=501" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')
        response = self.client.get("%s/locations/0,0/plots?max_plots=500" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_max_plots_param_cannot_be_less_than_1(self):
        response = self.client.get("%s/locations/0,0/plots?max_plots=0" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The max_plots parameter must be a number between 1 and 500')
        response = self.client.get("%s/locations/0,0/plots?max_plots=1" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 200)

    def test_locations_plots_endpoint_distance_param_must_be_a_number(self):
        response = self.client.get("%s/locations/0,0/plots?distance=foo" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'The distance parameter must be a number')
        response = self.client.get("%s/locations/0,0/plots?distance=42" % API_PFX, **self.sign)
        self.assertEqual(response.status_code, 200)

    def test_plots(self):
        plot = mkPlot(self.user)
        plot.present = True
        plot.save()

        response = self.client.get("%s/locations/%s,%s/plots" % (API_PFX, plot.geometry.x, plot.geometry.y), **self.sign)

        self.assertEqual(response.status_code, 200)
        json = loads(response.content)

class CreatePlotAndTree(TestCase):

    def setUp(self):
        setupTreemapEnv()

        self.user = User.objects.get(username="jim")
        self.user.set_password("password")
        self.user.save()
        self.sign = create_signer_dict(self.user)
        auth = base64.b64encode("jim:password")
        self.sign = dict(self.sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % auth)])

    def test_create_plot_with_tree(self):
        data = {
            "lon": 35,
            "lat": 25,
            "geocode_address": "1234 ANY ST",
            "edit_address_street": "1234 ANY ST",
            "tree": {
                "height": 10
            }
        }

        plot_count = Plot.objects.count()
        reputation_count = UserReputationAction.objects.count()

        response = post_json( "%s/plots"  % API_PFX, data, self.client, self.sign)

        self.assertEqual(201, response.status_code, "Create failed:" + response.content)

        # Assert that a plot was added
        self.assertEqual(plot_count + 1, Plot.objects.count())
        # Assert that reputation was added
        self.assertEqual(reputation_count + 1, UserReputationAction.objects.count())

        response_json = loads(response.content)
        self.assertTrue("ok" in response_json)
        id = response_json["ok"]
        plot = Plot.objects.get(pk=id)
        self.assertEqual(35.0, plot.geometry.x)
        self.assertEqual(25.0, plot.geometry.y)
        tree = plot.current_tree()
        self.assertIsNotNone(tree)
        self.assertEqual(10.0, tree.height)

    def test_create_plot_with_invalid_tree_returns_400(self):
        data = {
            "lon": 35,
            "lat": 25,
            "geocode_address": "1234 ANY ST",
            "edit_address_street": "1234 ANY ST",
            "tree": {
                "height": 1000000
            }
        }

        tree_count = Tree.objects.count()
        reputation_count = UserReputationAction.objects.count()

        response = post_json( "%s/plots"  % API_PFX, data, self.client, self.sign)

        self.assertEqual(400, response.status_code, "Expected creating a million foot tall tree to return 400:" + response.content)

        body_dict = loads(response.content)
        self.assertTrue('error' in body_dict, "Expected the body JSON to contain an 'error' key")
        errors = body_dict['error']
        self.assertTrue(len(errors) == 1, "Expected a single error message to be returned")
        self.assertEqual('Height is too large.', errors[0])

        # Assert that a tree was _not_ added
        self.assertEqual(tree_count, Tree.objects.count())
        # Assert that reputation was _not_ added
        self.assertEqual(reputation_count, UserReputationAction.objects.count())

    def test_create_plot_with_geometry(self):
        data = {
            "geometry": {
                "lon": 35,
                "lat": 25,
            },
            "geocode_address": "1234 ANY ST",
            "edit_address_street": "1234 ANY ST",
            "tree": {
                "height": 10
            }
        }

        plot_count = Plot.objects.count()
        reputation_count = UserReputationAction.objects.count()

        response = post_json( "%s/plots"  % API_PFX, data, self.client, self.sign)

        self.assertEqual(201, response.status_code, "Create failed:" + response.content)

        # Assert that a plot was added
        self.assertEqual(plot_count + 1, Plot.objects.count())
        # Assert that reputation was added
        self.assertEqual(reputation_count + 1, UserReputationAction.objects.count())

        response_json = loads(response.content)
        self.assertTrue("ok" in response_json)
        id = response_json["ok"]
        plot = Plot.objects.get(pk=id)
        self.assertEqual(35.0, plot.geometry.x)
        self.assertEqual(25.0, plot.geometry.y)
        tree = plot.current_tree()
        self.assertIsNotNone(tree)
        self.assertEqual(10.0, tree.height)

class UpdatePlotAndTree(TestCase):
    def setUp(self):
        setupTreemapEnv()
        settings.PENDING_ON = False

        self.user = User.objects.get(username="jim")
        self.user.set_password("password")
        self.user.save()
        self.sign = create_signer_dict(self.user)
        auth = base64.b64encode("jim:password")
        self.sign = dict(self.sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % auth)])

        self.public_user = User.objects.get(username="amy")
        self.public_user.set_password("password")
        self.public_user.save()
        self.public_user_sign = create_signer_dict(self.public_user)
        public_user_auth = base64.b64encode("amy:password")
        self.public_user_sign = dict(self.public_user_sign.items() + [("HTTP_AUTHORIZATION", "Basic %s" % public_user_auth)])

    def test_invalid_plot_id_returns_400_and_a_json_error(self):
        response = put_json( "%s/plots/0"  % API_PFX, {}, self.client, self.sign)
        self.assertEqual(400, response.status_code)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json)
        print("Received an error message as expected:\n" + response_json['error'])

    def test_update_plot(self):
        test_plot = mkPlot(self.user)
        test_plot.width = 1
        test_plot.length = 2
        test_plot.geocoded_address = 'foo'
        test_plot.save()
        self.assertEqual(50, test_plot.geometry.x)
        self.assertEqual(50, test_plot.geometry.y)
        self.assertEqual(1, test_plot.width)
        self.assertEqual(2, test_plot.length)
        self.assertEqual('foo', test_plot.geocoded_address)

        reputation_count = UserReputationAction.objects.count()

        updated_values = {'geometry': {'lat': 70, 'lon': 60}, 'plot_width': 11, 'plot_length': 22, 'geocoded_address': 'bar'}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(200, response.status_code)

        response_json = loads(response.content)
        self.assertEqual(70, response_json['geometry']['lat'])
        self.assertEqual(60, response_json['geometry']['lng'])
        self.assertEqual(11, response_json['plot_width'])
        self.assertEqual(22, response_json['plot_length'])
        self.assertEqual('bar', response_json['address'])
        self.assertEqual(reputation_count + 1, UserReputationAction.objects.count())

    def test_update_plot_with_pending(self):
        settings.PENDING_ON = True
        test_plot = mkPlot(self.user)
        test_plot.width = 1
        test_plot.length = 2
        test_plot.geocoded_address = 'foo'
        test_plot.save()
        self.assertEqual(50, test_plot.geometry.x)
        self.assertEqual(50, test_plot.geometry.y)
        self.assertEqual(1, test_plot.width)
        self.assertEqual(2, test_plot.length)
        self.assertEqual('foo', test_plot.geocoded_address)
        self.assertEqual(0, len(Pending.objects.all()), "Expected the test to start with no pending records")

        reputation_count = UserReputationAction.objects.count()

        updated_values = {'geometry': {'lat': 70, 'lon': 60}, 'plot_width': 11, 'plot_length': 22, 'geocoded_address': 'bar'}
        # Send the edit request as a public user
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.public_user_sign)
        self.assertEqual(200, response.status_code)

        # Assert that nothing has changed. Pends should have been created instead
        response_json = loads(response.content)
        self.assertEqual(50, response_json['geometry']['lat'])
        self.assertEqual(50, response_json['geometry']['lng'])
        self.assertEqual(1, response_json['plot_width'])
        self.assertEqual(2, response_json['plot_length'])
        self.assertEqual('foo', response_json['address'])
        self.assertEqual(reputation_count, UserReputationAction.objects.count())
        self.assertEqual(4, len(PlotPending.objects.all()), "Expected 4 pends, one for each edited field")

        self.assertEqual(4, len(response_json['pending'].keys()), "Expected the json response to have a pending dict with 4 keys, one for each field")

    def test_invalid_field_returns_200_field_is_not_in_response(self):
        test_plot = mkPlot(self.user)
        updated_values = {'foo': 'bar'}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(200, response.status_code)
        response_json = loads(response.content)
        self.assertFalse("error" in response_json.keys(), "Did not expect an error")
        self.assertFalse("foo" in response_json.keys(), "Did not expect foo to be added to the plot")

    def test_update_creates_tree(self):
        test_plot = mkPlot(self.user)
        test_plot_id = test_plot.id
        self.assertIsNone(test_plot.current_tree())
        updated_values = {'tree': {'dbh': 1.2}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(200, response.status_code)
        tree = Plot.objects.get(pk=test_plot_id).current_tree()
        self.assertIsNotNone(tree)
        self.assertEqual(1.2, tree.dbh)

    def test_update_creates_tree_with_pending(self):
        settings.PENDING_ON = True
        test_plot = mkPlot(self.user)
        test_plot_id = test_plot.id
        self.assertIsNone(test_plot.current_tree())
        self.assertEqual(0, len(Pending.objects.all()), "Expected the test to start with no pending records")

        updated_values = {'tree': {'dbh': 1.2}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.public_user_sign)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(Pending.objects.all()), "Expected a new tree to be created, rather than creating pends")
        tree = Plot.objects.get(pk=test_plot_id).current_tree()
        self.assertIsNotNone(tree)
        self.assertEqual(1.2, tree.dbh)

    def test_update_tree(self):
        test_plot = mkPlot(self.user)
        test_tree = mkTree(self.user, plot=test_plot)
        test_tree_id = test_tree.id
        test_tree.dbh = 2.3
        test_tree.save()

        updated_values = {'tree': {'dbh': 3.9}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(200, response.status_code)
        tree = Tree.objects.get(pk=test_tree_id)
        self.assertIsNotNone(tree)
        self.assertEqual(3.9, tree.dbh)

    def test_update_tree_with_pending(self):
        settings.PENDING_ON = True

        test_plot = mkPlot(self.user)
        test_tree = mkTree(self.user, plot=test_plot)
        test_tree_id = test_tree.id
        test_tree.dbh = 2.3
        test_tree.save()

        self.assertEqual(0, len(Pending.objects.all()), "Expected the test to start with no pending records")

        updated_values = {'tree': {'dbh': 3.9}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.public_user_sign)
        self.assertEqual(200, response.status_code)
        tree = Tree.objects.get(pk=test_tree_id)
        self.assertIsNotNone(tree)
        self.assertEqual(2.3, tree.dbh, "A pend should have been created instead of editing the tree value.")
        self.assertEqual(1, len(TreePending.objects.all()), "Expected 1 pend record for the edited field.")

        response_json = loads(response.content)
        self.assertEqual(1, len(response_json['tree']['pending'].keys()), "Expected the json response to have a tree.pending dict with 1 keys")

    def test_update_tree_species(self):
        test_plot = mkPlot(self.user)
        test_tree = mkTree(self.user, plot=test_plot)
        test_tree_id = test_tree.id

        first_species = Species.objects.all()[0]
        updated_values = {'tree': {'species': first_species.id}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(200, response.status_code)
        tree = Tree.objects.get(pk=test_tree_id)
        self.assertIsNotNone(tree)
        self.assertEqual(first_species, tree.species)

    def test_update_tree_returns_400_on_invalid_species_id(self):
        test_plot = mkPlot(self.user)
        mkTree(self.user, plot=test_plot)

        invalid_species_id = -1
        self.assertRaises(Exception, Species.objects.get, pk=invalid_species_id)

        updated_values = {'tree': {'species': invalid_species_id}}
        response = put_json( "%s/plots/%d"  % (API_PFX, test_plot.id), updated_values, self.client, self.sign)
        self.assertEqual(400, response.status_code)
        response_json = loads(response.content)
        self.assertTrue("error" in response_json.keys(), "Expected an 'error' key in the JSON response")
