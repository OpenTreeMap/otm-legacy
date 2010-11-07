import os
from django.test import Client, TestCase
import simplejson

# http://www.djangoproject.com/documentation/models/test_client/

USER = 'dane'
PASS = 'dane'

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Log in
        # requires a fixture of this user to be loaded into test database...
        login = self.client.login(username=USER, password=PASS)
        self.failUnless(login, 'Could not log in')
        
    def object_update(self,data):
        
        response = self.client.post('/update/',data=data,content_type='application/javascript; charset=utf8')
        
        # make sure we get proper response
        self.failUnlessEqual(response.status_code, 200)
        
        json = simplejson.loads(response.content)
        
        # make sure we get json dict back
        self.failUnlessEqual(isinstance(json,dict), True)

        self.failUnlessEqual(json['success'], True)
    
    def test_tree_update(self):
        json = simplejson.loads('{"model": "Tree", "update": {"powerline_conflict_potential": false}, "id": "105"}')
        return self.object_update(json)

    def test_tree_status_update(self):
        json = {"model":"TreeStatus","update":{"value":55,"key":"dbh"},"parent":{"model":"Tree","id":105}}
        return self.object_update(json)

    def test_tree_alert_update(self):
        json = {"model":"TreeAlert","update":{"value":"2010-02-21","key":"needs_watering"},"parent":{"model":"Tree","id":1000}}
        return self.object_update(json)
        
    def test_tree_species_update(self):
        json = {"model":"Tree","update":{"species_id":21534},"id":31793}
        return self.object_update(json)        