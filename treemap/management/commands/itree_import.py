from os.path import dirname
import operator
from decimal import *
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from treemap.models import Resource

class Command(BaseCommand):
    args = '<input_file_name, column_name>'
    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose debug text'),
    )

    def get_dbf_rows(self, in_file):
        reader = dbf.Dbf(in_file)
        print 'Opening input file: %s ' % in_file

        self.headers = reader.fieldNames
        self.err_writer.writerow(self.headers)
        
        print 'Converting input file to dictionary'
        rows = []
        for dbf_row in reader:
            d = {}
            for name in self.headers:
                d[name] = dbf_row[name]
            rows.append(d)
        return rows
    
    def get_csv_rows(self, in_file):
        reader = csv.DictReader(open(in_file, 'r' ), restval=123)
        print 'Opening input file: %s ' % in_file

        rows = list(reader)
                
        self.headers = reader.fieldnames
        self.err_writer.writerow(self.headers)        
                
        return rows
    
    def handle(self, *args, **options):
        try:    
            self.file_name = args[0]
            self.column_name = args[1]
            in_file = dirname(__file__) + "/" + self.file_name
            err_file = dirname(__file__) + "/" + self.file_name + ".err"
            self.verbose = options.get('verbose')
        except:
            print "Arguments:  Input_File_Name.[dbf|csv], column name"
            print "Options:    --verbose, --insert"
            return
        
        self.err_writer = csv.writer(open(err_file, 'wb'))
        
        if self.file_name.endswith('.csv'):
            rows = self.get_csv_rows(in_file)
        if self.file_name.endswith('.dbf'):
            rows = self.get_dbf_rows(in_file)
        
        print 'Importing %d species' % len(rows)
        for i, row in enumerate(rows):
            self.handle_row(row)
            
            j = i + 1
            if j % 50 == 0:
               print 'Loaded %d...' % j
            self.log_verbose("item %d" % i)
        
        print "Finished data load. "
    
    def log_verbose(self, msg):
        if self.verbose: print msg
    
    def log_error(self, msg, row):
        print "ERROR: %s" % msg
        columns = [row[s] for s in self.headers]
        self.err_writer.writerow(columns)
    
    def check_resource(self, row):
        # locate the species and instanciate the tree instance
        
        if not row["code"]:            
            self.log_verbose("  No code column found")
            return (False, None)

        code = row['code']
       
        self.log_verbose("  Looking for species code: %s" % code)
        found = Resource.objects.filter(meta_species__iexact=code)
    
        if found: #species match found
            self.log_verbose("  Found species code %r" % found[0])
            return (True, found[0])
            
        #species data but no match, add it
        self.log_verbose("  Adding unknown species code %s " % code) 
        resource = Resource(meta_species=code, region="NorthernCalifornia")
        return (True, resource)

    
    def handle_row(self, row):
        self.log_verbose(row)
        
        # check the species (if any)
        ok, resource = self.check_resource(row)
        if not ok: return
        
        dbh_list = [3.81,11.43,22.86,38.10,53.34,68.58,83.82,99.06,114.30]
        if len(row)-1 > 10:
            dbh_list = [2.54,5.08,7.62,10.16,12.7,15.24,17.78,20.32,22.86,25.4,27.94,30.48,33.02,35.56,38.1,40.64,43.18,45.72,48.26,50.8,53.34,55.88,58.42,60.96,63.5,66.04,68.58,71.12,73.66,76.2,78.74,81.28,83.82,86.36,88.9,91.44,93.98,96.52,99.06,101.6,104.14,106.68,109.22,111.76,114.3]
        data = []
        for dbh in dbh_list:
            for value in row:
                if value == 'code': continue
                test = float(value)
                if dbh == test:
                    data.append(float(row[value]))
        self.log_verbose("  Final data %s" % data)    
        setattr(resource, self.column_name, data.__str__())
        
        resource.save()

