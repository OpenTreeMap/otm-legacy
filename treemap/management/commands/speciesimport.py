from os.path import dirname
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from UrbanForestMap.treemap.models import Species, Resource

class Command(BaseCommand):
    args = '<input_file_name>'
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
            in_file = dirname(__file__) + "/" + self.file_name
            err_file = dirname(__file__) + "/" + self.file_name + ".err"
            self.verbose = options.get('verbose')
        except:
            print "Arguments:  Input_File_Name.[dbf|csv]"
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
    
    def check_species(self, row):
        # locate the species and instanciate the tree instance
        
        if not row["genus"]:            
            self.log_verbose("  No genus information")
            return (False, None)

        genus = row['genus']
        name = '%s' % genus
        species = ''
        cultivar = ''
        if row.get('species'):
            species = row['species']
            name += " %s" % species
        if row.get('cultivar'):
            cultivar = row['cultivar']
            name += " %s" % cultivar

        self.log_verbose("  Looking for species: %s" % name)
        found = Species.objects.filter(genus__iexact=genus).filter(species__iexact=species).filter(cultivar_name__iexact=cultivar)
    
        if found: #species match found
            self.log_verbose("  Found species %r" % found[0])
            return (True, found[0])
            
        #species data but no match, add it
        self.log_verbose("  Adding unknown species %s %s %s" % (genus, species, cultivar)) 
        species = Species(genus=genus, species=species, cultivar_name=cultivar, scientific_name=name)
        return (True, species)

    
    def handle_row(self, row):
        self.log_verbose(row)
        
        # check the species (if any)
        ok, species = self.check_species(row)
        if not ok: return

        
        if row.get('common_name'):
            species.common_name = row['common_name']

        if row.get('usda_code'):
            species.symbol = row['usda_code']
        if row.get('itree_code'):
            species.itree_code = row['itree_code']
        if row.get('flowering'):
            species.flower_conspicuous = row['flowering'] == 'yes'
        if row.get('flower_time'):
            species.bloom_period = row['flower_time']
        if row.get('fall_color'):
            species.fall_conspicuous = row['fall_color'] == 'yes'
        if row.get('edible'):
            species.palatable_human = row['edible'] == 'yes'
        if row.get('fruiting_time'):
            species.fruit_period = row['fruiting_time']
        if row.get('wildlife'):
            species.wildlife_value = row['wildlife'] == 'yes'
        if row.get('native'):
            species.native_status = row['native'] == 'yes'
        if row.get('webpage_link'):
            species.fact_sheet = row['webpage_link']
        
        species.save()

        resource = Resource.objects.get(meta_species=species.itree_code)
        if resource:
            species.resource.clear()
            species.resource.add(resource)
        else:
            self.log_error("WARNING: No resource found for code %s" % species.itree_code, row)

