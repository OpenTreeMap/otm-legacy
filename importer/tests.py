from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon, Polygon, Point

import tempfile
import csv
import json
from datetime import date

from StringIO import StringIO

# Since OTM is such a crazy huge beast, we'll use the same functions
# the API does for setting up a reasonable env
from api.test_utils import setupTreemapEnv, mkPlot

from importer.views import create_rows_for_event, validate_main_file, \
    Errors, validate_row, process_csv, process_status, process_commit

from importer.models import TreeImportEvent, TreeImportRow
from treemap.models import Species, Neighborhood, Plot, ExclusionMask

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

        # If we add an exclusion zone, it should fail
        egeom = MultiPolygon(Polygon(
            ((10,10),(10,30),(30,30),(30,10),(10,10))))

        e = ExclusionMask(geometry=egeom, type='blah blah')
        e.save()

        i = mkpt(25,25)
        r = validate_row(i)

        self.assertNotHasError(i, Errors.GEOM_OUT_OF_BOUNDS)
        self.assertNotHasError(i, Errors.INVALID_GEOM)
        self.assertNotHasError(i, Errors.FLOAT_ERROR)
        self.assertHasError(i, Errors.EXCL_ZONE)


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

    def run_through_commit_views(self, csv):
        r = self.create_csv_request(csv, name='some name')
        resp = process_csv(r)
        j = json.loads(resp.content)

        pk = j['id']

        process_commit(None, pk)
        return pk

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
        | 34.2    | 29.2    | 12       |
        | 19.2    | 27.2    | 14       |
        """

        j = self.run_through_process_views(csv)

        self.assertEqual({'status': 'success', 'rows': 2}, j)

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)

        rows = ie.treeimportrow_set.order_by('idx').all()

        self.assertEqual(len(rows), 2)

        plot1, plot2 = [r.plot for r in rows]
        self.assertIsNotNone(plot1)
        self.assertIsNotNone(plot2)

        self.assertEqual(int(plot1.geometry.x*10), 342)
        self.assertEqual(int(plot1.geometry.y*10), 292)
        self.assertEqual(plot1.current_tree().dbh, 12)

        self.assertEqual(int(plot2.geometry.x*10), 192)
        self.assertEqual(int(plot2.geometry.y*10), 272)
        self.assertEqual(plot2.current_tree().dbh, 14)

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
        | 32.1    | 22.4    | 15       | true      | Dead      |       |         |
        | 33.2    | 19.1    | 32       | true      | Arg       |       |         |
        | 33.2    | q19.1   | -33.3    | true      | Dead      | gfail |         |
        | 32.1    | 12.1    |          | false     | Dead      | g1    | 200     |
        | 32.1    | 12.1    | 300      | false     | Dead      | g1    |         |
        | 11.1    | 12.1    |          | false     | Dead      |       |         |
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
        self.assertEqual(errors['7'],
                         {(Errors.EXCL_ZONE[0], None)})

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

    def test_all_tree_data(self):
        s1_gsc = Species(symbol='S1G__', scientific_name='',
                         genus='g1', species='s1', cultivar_name='c1')
        s1_gsc.save()

        csv = """
        | point x | point y | tree owner | tree steward | diameter | tree height |
        | 45.53   | 31.1    | jimmy      | jane         | 23.1     | 90.1        |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        tree = ie.treeimportrow_set.all()[0].plot.current_tree()

        self.assertEqual(tree.tree_owner, 'jimmy')
        self.assertEqual(tree.steward_name, 'jane')
        self.assertEqual(tree.dbh, 23.1)
        self.assertEqual(tree.height, 90.1)

        csv = """
        | point x | point y | canopy height | genus | species | cultivar |
        | 45.59   | 31.1    | 112           |       |         |          |
        | 45.58   | 33.9    |               | g1    | s1      | c1       |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        rows = ie.treeimportrow_set.order_by('idx').all()
        tree1 = rows[0].plot.current_tree()
        tree2 = rows[1].plot.current_tree()

        self.assertEqual(tree1.canopy_height, 112)
        self.assertIsNone(tree1.species)

        self.assertEqual(tree2.species.pk, s1_gsc.pk)

        csv = """
        | point x | point y | tree sponsor | date planted | read only | tree url    |
        | 45.12   | 55.12   | treeluvr     | 2012-02-03   | true      | http://spam |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        tree = ie.treeimportrow_set.all()[0].plot.current_tree()

        dateplanted = date(2012,2,3)

        self.assertEqual(tree.sponsor, 'treeluvr')
        self.assertEqual(tree.date_planted, dateplanted)
        self.assertEqual(tree.readonly, True)
        self.assertEqual(tree.url, 'http://spam')

        csv = """
        | point x | point y | condition | canopy condition | pests and diseases | local projects |
        | 45.66   | 53.13   | Dead      | %s               | %s                 | %s             |
        """ % ('Full - No Gaps', 'Phytophthora alni', 'San Francisco Landmark')


        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        tree = ie.treeimportrow_set.all()[0].plot.current_tree()

        self.assertEqual(tree.condition, 'Dead')
        self.assertEqual(tree.canopy_condition, 'Full - No Gaps')
        self.assertEqual(tree.pests, 'Phytophthora alni')

        #TODO: Projects and Actions work differently...
        #      need to handle those cases
        # self.assertEqual(tree.projects, 'San Francisco Landmark')


    def test_all_plot_data(self):
        csv = """
        | point x | point y | plot width | plot length | plot type | read only |
        | 45.53   | 31.1    | 19.2       | 13          | Other     | false     |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        plot = ie.treeimportrow_set.all()[0].plot

        self.assertEqual(int(plot.geometry.x*100), 4553)
        self.assertEqual(int(plot.geometry.y*100), 3110)
        self.assertEqual(plot.width, 19.2)
        self.assertEqual(plot.length, 13)
        self.assertEqual(plot.type, '10')
        self.assertEqual(plot.readonly, False)

        csv = """
        | point x | point y | sidewalk           | powerline conflict | notes |
        | 45.53   | 31.1    | Minor or No Damage | No                 | anote |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        plot = ie.treeimportrow_set.all()[0].plot

        self.assertEqual(plot.sidewalk_damage, '1')
        self.assertEqual(plot.powerline_conflict_potential, '2')
        self.assertEqual(plot.owner_additional_properties, 'anote')

        csv = """
        | point x | point y | original id number | data source |
        | 45.53   | 31.1    | 443                | trees r us  |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)
        plot = ie.treeimportrow_set.all()[0].plot

        self.assertEqual(plot.owner_orig_id, '443')
        self.assertEqual(plot.owner_additional_id, 'trees r us')

    def test_override_with_opentreemap_id(self):
        p1 = mkPlot(self.user, geom=Point(55.0,25.0))
        p1.save()

        csv = """
        | point x | point y | opentreemap id number | data source |
        | 45.53   | 31.1    | %s                    | trees r us  |
        """ % p1.pk

        self.run_through_commit_views(csv)

        p1b = Plot.objects.get(pk=p1.pk)
        self.assertEqual(int(p1b.geometry.x*100), 4553)
        self.assertEqual(int(p1b.geometry.y*100), 3110)

    def test_tree_present_works_as_expected(self):
        csv = """
        | point x | point y | tree present | diameter |
        | 45.53   | 31.1    | false        |          |
        | 45.63   | 32.1    | true         |          |
        | 45.73   | 33.1    | true         | 23       |
        | 45.93   | 33.1    | false        | 23       |
        """

        ieid = self.run_through_commit_views(csv)
        ie = TreeImportEvent.objects.get(pk=ieid)

        tests = [a.plot.current_tree() is not None
                 for a in ie.treeimportrow_set.all()]

        self.assertEqual(tests,
                         [False, # No tree data and tree present is false
                          True,  # Force a tree in this spot (tree present=true)
                          True,  # Data, so ignore tree present settings
                          True])  # Data, so ignore tree present settings
