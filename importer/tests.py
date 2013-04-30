from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon, Polygon, Point

import tempfile
import csv
import json

from StringIO import StringIO

# Since OTM is such a crazy huge beast, we'll use the same functions
# the API does for setting up a reasonable env
from api.test_utils import setupTreemapEnv, mkPlot

from importer.views import create_rows_for_event, validate_main_file, \
    Errors, validate_row, process_csv, process_status

from importer.models import TreeImportEvent, TreeImportRow
from treemap.models import Species, Neighborhood, Plot

class ValidationTest(TestCase):
    def setUp(self):
        self.user = User(username='smith')
        self.user.save()

        self.ie = TreeImportEvent(file_name='file',
                                  owner=self.user)
        self.ie.save()

    def mkrow(self,data):
        return TreeImportRow.objects.create(
            data=json.dumps(data), import_event=self.ie, idx=1)

    def assertHasError(self, thing, err, data=None, df=None):
        errors = ''
        errn,msg,fatal = err
        if thing.errors:
            errors = json.loads(thing.errors)
            for e in errors:
                if e['code'] == errn:
                    if data is not None:
                        edata = e['data']
                        if df:
                            edata = df(edata)
                        self.assertEqual(edata, data)
                    return

        raise AssertionError('Error code %s not found in %s' % (errn,errors))

    def assertNotHasError(self, thing, err, data=None):
        errn,msg,fatal = err
        if thing.errors:
            errors = json.loads(thing.errors)
            for e in errors:
                if e['code'] == errn:
                    raise AssertionError('Error code %s found in %s' % (errn,errors))

    def test_species_dbh_and_height(self):
        s1_gsc = Species(symbol='S1G__', scientific_name='',
                         genus='g1', species='s1', cultivar_name='c1',
                         v_max_height=30, v_max_dbh=19)
        s1_gs = Species(symbol='S1GS_', scientific_name='',
                        genus='g1', species='s1', cultivar_name='',
                        v_max_height=22, v_max_dbh=12)
        s1_gsc.save()
        s1_gs.save()

        row = {'point x': '16',
               'point y': '20',
               'genus': 'g1',
               'species': 's1',
               'diameter': '15',
               'tree height': '18'}

        i = self.mkrow(row)
        r = validate_row(i)

        self.assertHasError(i, Errors.SPECIES_DBH_TOO_HIGH)
        self.assertNotHasError(i, Errors.SPECIES_HEIGHT_TOO_HIGH)

        row['tree height'] = 25
        i = self.mkrow(row)
        r = validate_row(i)

        self.assertHasError(i, Errors.SPECIES_DBH_TOO_HIGH)
        self.assertHasError(i, Errors.SPECIES_HEIGHT_TOO_HIGH)

        row['cultivar'] = 'c1'
        i = self.mkrow(row)
        r = validate_row(i)

        self.assertNotHasError(i, Errors.SPECIES_DBH_TOO_HIGH)
        self.assertNotHasError(i, Errors.SPECIES_HEIGHT_TOO_HIGH)

    def test_proximity(self):
        setupTreemapEnv()

        user = User.objects.get(username="jim")
        p1 = mkPlot(user, geom=Point(25.0000001,25.0000001))
        p1.save()

        p2 = mkPlot(user, geom=Point(25.0000002,25.0000002))
        p2.save()

        p3 = mkPlot(user, geom=Point(25.0000003,25.0000003))
        p3.save()

        p4 = mkPlot(user, geom=Point(27.0000001,27.0000001))
        p4.save()

        n1 = { p.pk for p in [p1,p2,p3] }
        n2 = { p4.pk }

        i = self.mkrow({'point x': '25.00000025',
                        'point y': '25.00000025'})
        r = validate_row(i)

        self.assertHasError(i, Errors.NEARBY_TREES, n1, set)

        i = self.mkrow({'point x': '27.00000015',
                        'point y': '27.00000015'})
        r = validate_row(i)

        self.assertHasError(i, Errors.NEARBY_TREES, n2, set)

        i = self.mkrow({'point x': '30.00000015',
                        'point y': '30.00000015'})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.NEARBY_TREES)


    def test_species_id(self):
        s1_gsc = Species(symbol='S1G__', scientific_name='',
                         genus='g1', species='s1', cultivar_name='c1')
        s1_gs = Species(symbol='S1GS_', scientific_name='',
                        genus='g1', species='s1', cultivar_name='')
        s1_g = Species(symbol='S1GSC', scientific_name='',
                       genus='g1', species='', cultivar_name='')

        s2_gsc = Species(symbol='S2GSC', scientific_name='',
                         genus='g2', species='s2', cultivar_name='c2')
        s2_gs = Species(symbol='S2GS_', scientific_name='',
                        genus='g2', species='s2', cultivar_name='')

        for s in [s1_gsc, s1_gs, s1_g, s2_gsc, s2_gs]:
            s.save()

        # Simple genus, species, cultivar matches
        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'genus': 'g1'})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.INVALID_SPECIES)

        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'genus': 'g1',
                        'species': 's1'})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.INVALID_SPECIES)

        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'genus': 'g1',
                        'species': 's1',
                        'cultivar': 'c1'})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.INVALID_SPECIES)

        # Test no species info at all
        i = self.mkrow({'point x': '16',
                        'point y': '20'})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.INVALID_SPECIES)

        # Test mismatches
        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'genus': 'g1',
                        'species': 's2',
                        'cultivar': 'c1'})
        r = validate_row(i)

        self.assertHasError(i, Errors.INVALID_SPECIES)

        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'genus': 'g2'})
        r = validate_row(i)

        self.assertHasError(i, Errors.INVALID_SPECIES)


    def test_otm_id(self):
        # silly invalid-int-errors should be caught
        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'opentreemap id number': '44b'})
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.INT_ERROR, 'opentreemap id number')

        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'opentreemap id number': '-22'})
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.POS_INT_ERROR, 'opentreemap id number')

        # With no plots in the system, all ids should fail
        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'opentreemap id number': '44'})
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.INVALID_OTM_ID, 44)

        # Add in plot
        setupTreemapEnv() # We need the whole darn thing
                          # just so we can add a plot :(

        # SetupTME provides a special user for us to use
        # as well as particular neighborhood
        user = User.objects.get(username="jim")
        p = mkPlot(user, geom=Point(25,25))
        p.save()

        # With an existing plot it should be fine
        i = self.mkrow({'point x': '16',
                        'point y': '20',
                        'opentreemap id number': p.pk})
        r = validate_row(i)

        self.assertNotHasError(i, Errors.INVALID_OTM_ID)
        self.assertNotHasError(i, Errors.INT_ERROR)

    def test_geom_validation(self):
        def mkpt(x,y):
            return self.mkrow({'point x': str(x), 'point y': str(y)})

        # Invalid numbers
        i = mkpt('300a','20b')
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.FLOAT_ERROR)

        # Crazy lat/lngs
        i = mkpt(300,20)
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.INVALID_GEOM)

        i = mkpt(50,93)
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.INVALID_GEOM)

        # Out of neighborhood (neighborhood created in setUp)
        ngeom = MultiPolygon(Polygon(
            ((0, 0), (0, 50), (50, 50), (50, 0), (0, 0))))

        neighborhood = Neighborhood(
            name='test neighborhood',
            region_id=34,
            city='blah',
            county='blarg',
            geometry=ngeom)

        neighborhood.save()

        i = mkpt(55,55)
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.GEOM_OUT_OF_BOUNDS)

        i = mkpt(-5,-5)
        r = validate_row(i)

        self.assertFalse(r)
        self.assertHasError(i, Errors.GEOM_OUT_OF_BOUNDS)

        # This should work...
        i = mkpt(25,25)
        r = validate_row(i)

        # Can't assert that r is true because other validation
        # logic may have tripped it
        self.assertNotHasError(i, Errors.GEOM_OUT_OF_BOUNDS)
        self.assertNotHasError(i, Errors.INVALID_GEOM)
        self.assertNotHasError(i, Errors.FLOAT_ERROR)

class FileLevelValidationTest(TestCase):
    def write_csv(self, stuff):
        t = tempfile.NamedTemporaryFile()

        with open(t.name,'w') as csvfile:
            w = csv.writer(csvfile)
            for r in stuff:
                w.writerow(r)

        return t

    def setUp(self):
        self.user = User(username='smith')
        self.user.save()


    def test_empty_file_error(self):
        ie = TreeImportEvent(file_name='file',
                             owner=self.user)
        ie.save()

        base_rows = TreeImportRow.objects.count()

        c = self.write_csv([['header_field1','header_fields2','header_field3']])

        create_rows_for_event(ie, c)
        rslt = validate_main_file(ie)

        # No rows added and validation failed
        self.assertEqual(TreeImportRow.objects.count(), base_rows)
        self.assertFalse(rslt)

        errors = json.loads(ie.errors)

        # The only error is a bad file error
        self.assertTrue(len(errors), 1)
        etpl = (errors[0]['code'], errors[0]['msg'], True)

        self.assertEqual(etpl, Errors.EMPTY_FILE)


    def test_missing_point_field(self):
        ie = TreeImportEvent(file_name='file',
                             owner=self.user)
        ie.save()

        base_rows = TreeImportRow.objects.count()

        c = self.write_csv([['address','plot width','plot_length'],
                            ['123 Beach St','5','5'],
                            ['222 Main St','8','8']])

        create_rows_for_event(ie, c)
        rslt = validate_main_file(ie)

        self.assertFalse(rslt)

        errors = json.loads(ie.errors)

        # Should be x/y point error
        self.assertTrue(len(errors), 1)
        etpl = (errors[0]['code'], errors[0]['msg'], True)

        self.assertEqual(etpl, Errors.MISSING_POINTS)

    def test_unknown_field(self):
        ie = TreeImportEvent(file_name='file',
                             owner=self.user)
        ie.save()

        base_rows = TreeImportRow.objects.count()

        c = self.write_csv([['address','name','age','point x','point y'],
                            ['123 Beach St','a','b','5','5'],
                            ['222 Main St','a','b','8','8']])

        create_rows_for_event(ie, c)
        rslt = validate_main_file(ie)

        self.assertFalse(rslt)

        errors = json.loads(ie.errors)

        # Should be x/y point error
        self.assertTrue(len(errors), 1)
        etpl = (errors[0]['code'], errors[0]['msg'], False)

        self.assertEqual(etpl, Errors.UNMATCHED_FIELDS)
        self.assertEqual(set(errors[0]['data']), set(['name','age']))

class IntegrationTests(TestCase):
    def setUp(self):
        setupTreemapEnv()

        self.user = User.objects.get(username='jim')

    def create_csv_stream(self, stuff):
        csvfile = StringIO()

        w = csv.writer(csvfile)
        for r in stuff:
            w.writerow(r)

        return StringIO(csvfile.getvalue())

    def create_csv_request(self, stuff, **kwargs):
        rows = [[z.strip() for z in a.split('|')[1:-1]]
                for a in stuff.split('\n') if len(a.strip()) > 0]

        req = HttpRequest()
        req.FILES = {'filename': self.create_csv_stream(rows)}
        req.REQUEST = kwargs

        return req

    def run_through_process_views(self, csv):
        r = self.create_csv_request(csv, name='some name')
        resp = process_csv(r)
        j = json.loads(resp.content)

        pk = j['id']

        resp = process_status(None, pk)
        return json.loads(resp.content)

    def extract_errors(self, json):
        errors = {}
        for k,v in json['errors'].iteritems():
            errors[k] = set()
            for e in v:
                d = e['data']
                if isinstance(d,list):
                    d = tuple(d) # Freeze

                errors[k].add((e['code'], d))

        return errors

    def test_noerror_load(self):
        csv = """
        | point x | point y | diameter |
        | 34.2    | 24.2    | 12       |
        | 19.2    | 23.2    | 14       |
        """

        j = self.run_through_process_views(csv)
        self.assertEqual({'status': 'success', 'rows': 2}, j)

    def test_bad_structure(self):
        # Point Y -> PointY, expecting two errors
        csv = """
        | point x | pointy | diameter |
        | 34.2    | 24.2   | 12       |
        | 19.2    | 23.2   | 14       |
        """

        j = self.run_through_process_views(csv)
        self.assertEqual(len(j['errors']), 2)
        self.assertEqual({e['code'] for e in j['errors']},
                         {Errors.MISSING_POINTS[0],
                          Errors.UNMATCHED_FIELDS[0]})

    def test_faulty_data1(self):
        s1_g = Species(symbol='S1GSC', scientific_name='',
                       genus='g1', species='', cultivar_name='',
                       v_max_dbh=50.0, v_max_height=100.0)
        s1_g.save()

        csv = """
        | point x | point y | diameter | read only | condition | genus | tree height |
        | -34.2   | 24.2    | q12      | true      | Dead      |       |         |
        | 323     | 23.2    | 14       | falseo    | Critical  |       |         |
        | 22.1    | 22.4    | 15       | true      | Dead      |       |         |
        | 23.2    | 19.1    | 32       | true      | Arg       |       |         |
        | 23.2    | q19.1   | -33.3    | true      | Dead      | gfail |         |
        | 22.1    | 12.1    |          | false     | Dead      | g1    | 200     |
        | 22.1    | 12.1    | 300      | false     | Dead      | g1    |         |
        """

        j = self.run_through_process_views(csv)
        errors = self.extract_errors(j)
        self.assertEqual(errors['0'],
                         {(Errors.GEOM_OUT_OF_BOUNDS[0], None),
                          (Errors.FLOAT_ERROR[0], 'diameter')})
        self.assertEqual(errors['1'],
                         {(Errors.INVALID_GEOM[0], None),
                          (Errors.BOOL_ERROR[0], 'read only')})
        self.assertNotIn('2', errors)
        self.assertEqual(errors['3'],
                         {(Errors.INVALID_CHOICE[0], 'conditions')})
        self.assertEqual(errors['4'],
                         {(Errors.INVALID_SPECIES[0], 'gfail'),
                          (Errors.FLOAT_ERROR[0], 'point y'),
                          (Errors.POS_FLOAT_ERROR[0], 'diameter'),
                          (Errors.MISSING_POINTS[0], None)})
        self.assertEqual(errors['5'],
                         {(Errors.SPECIES_HEIGHT_TOO_HIGH[0], 100.0)})
        self.assertEqual(errors['6'],
                         {(Errors.SPECIES_DBH_TOO_HIGH[0], 50.0)})

    def test_faulty_data2(self):
        p1 = mkPlot(self.user, geom=Point(25.0000001,25.0000001))
        p1.save()

        string_too_long = 'a' * 256

        csv = """
        | point x    | point y    | opentreemap id number | tree steward | date planted |
        | 25.0000002 | 25.0000002 |          |              | 2012-02-18 |
        | 25.1000002 | 25.1000002 | 133      |              |            |
        | 25.1000002 | 25.1000002 | -3       |              | 2023-FF-33 |
        | 25.1000002 | 25.1000002 | bar      |              | 2012-02-91 |
        | 25.1000002 | 25.1000002 | %s       | %s           |            |
        """ % (p1.pk, string_too_long)


        j = self.run_through_process_views(csv)
        errors = self.extract_errors(j)
        self.assertEqual(errors['0'],
                         {(Errors.NEARBY_TREES[0], (p1.pk,))})
        self.assertEqual(errors['1'],
                         {(Errors.INVALID_OTM_ID[0], 133)})
        self.assertEqual(errors['2'],
                         {(Errors.POS_INT_ERROR[0], 'opentreemap id number'),
                          (Errors.INVALID_DATE[0], 'date planted')})
        self.assertEqual(errors['3'],
                         {(Errors.INT_ERROR[0], 'opentreemap id number'),
                          (Errors.INVALID_DATE[0], 'date planted')})
        self.assertEqual(errors['4'],
                         {(Errors.STRING_TOO_LONG[0], 'tree steward')})
