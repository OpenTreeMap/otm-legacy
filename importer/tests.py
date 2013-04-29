from django.test import TestCase
from django.contrib.auth.models import User

import tempfile
import csv
import json

from importer.views import create_rows_for_event, validate_main_file, Errors
from importer.models import TreeImportEvent, TreeImportRow

class IncomingFileTest(TestCase):
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

        create_rows_for_event(ie, c.name)
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

        create_rows_for_event(ie, c.name)
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

        create_rows_for_event(ie, c.name)
        rslt = validate_main_file(ie)

        self.assertFalse(rslt)

        errors = json.loads(ie.errors)

        # Should be x/y point error
        self.assertTrue(len(errors), 1)
        etpl = (errors[0]['code'], errors[0]['msg'], False)

        self.assertEqual(etpl, Errors.UNMATCHED_FIELDS)
        self.assertEqual(set(errors[0]['data']), set(['name','age']))
