from os.path import dirname
import operator
from decimal import *
import csv
import os.path
import os
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from OpenTreeMap.treemap.models import Resource

class Command(BaseCommand):
    args = '<input_file_name, column_name>'
    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose debug text'),
    )

    def write_headers_if_needed(self):
        if not self.wrote_headers:
            self.err_writer.writerow(self.headers)
            self.wrote_headers = True

    def get_dbf_rows(self, in_file):
        reader = dbf.Dbf(in_file)
        print 'Opening input file: %s ' % in_file

        self.headers = reader.fieldNames
        
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
                
        return rows
    
    def name2column(self, name):
        match_dict = {
            "AQ_NOx_avoided.csv": "aq_nox_avoided_dbh",
            "AQ_PM10_avoided.csv": "aq_pm10_avoided_dbh",
            "AQ_SOx_dep.csv": "aq_sox_dep_dbh",
            "CO2_avoided.csv": "co2_avoided_dbh",
            "Electricity.csv": "electricity_dbh",
            "AQ_NOx_dep.csv": "aq_nox_dep_dbh",
            "AQ_PM10_dep.csv": "aq_pm10_dep_dbh",
            "AQ_VOC_avoided.csv": "aq_voc_avoided_dbh",
            "CO2_sequestered.csv": "co2_sequestered_dbh",
            "Hydro_Interception.csv": "hydro_interception_dbh",
            "AQ_Ozone_dep.csv": "aq_ozone_dep_dbh",
            "AQ_SOx_avoided.csv": "aq_sox_avoided_dbh",
            "BVOC.csv": "bvoc_dbh",
            "CO2_storage.csv": "co2_storage_dbh",
            "Natural_Gas.csv": "natural_gas_dbh" }

        if name in match_dict:
            return match_dict[name]
        else:
            raise Exception("You must either provide a standard "
                            "itree name (see below) or provide the "
                            "database column to write to. \n\n"
                            "Possible csv names: %s\n" % match_dict.keys() +
                            "Possible columns: %s\n" % match_dict.values())



    def handle(self, *args, **options):
        try:                
            self.verbose = options.get('verbose')            

            self.file_name = args[0]

            if os.path.isdir(self.file_name):
                self.process_dir(self.file_name)
            else:
                if len(args) == 1:
                    self.column_name = self.name2column(os.path.split(self.file_name)[1])
                else:
                    self.column_name = args[1]

                self.process_file(self.file_name)
        except Exception, e:
            raise
            print "Arguments:  Input_File_Name.[dbf|csv], column name"
            print "Options:    --verbose"

    def process_dir(self, adir):
        for f in os.listdir(adir):
            try:
                if f.endswith(".csv"):
                    f = adir + f
                    self.column_name = self.name2column(os.path.split(f)[1])
                    self.file_name = f
                    print "Processing %s (%s)" % (f, self.column_name)
                    self.process_file(f)
            except Exception, e:
                raise
                pass            

    def process_file(self, in_file):
        self.wrote_headers = False
        in_file = self.file_name
        err_file = in_file + ".err"
        
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

        self.write_headers_if_needed(self)
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
        
        dbh_list = [3.81,11.43,22.86,38.10,53.34,68.58,83.82,99.06,114.3]
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

