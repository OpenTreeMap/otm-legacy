from os.path import dirname
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from UrbanForestMap.treemap.models import Species, Tree, Neighborhood, ZipCode, TreeStatus, Choices, ImportEvent

class Command(BaseCommand):
    args = '<input_file_name, data_owner_id>'
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
            in_file = dirname(__file__) + "\\" + self.file_name
            err_file = dirname(__file__) + "\\" + self.file_name + ".err"
            self.verbose = options.get('verbose')
            self.user_id = args[1]
        except:
            print "Arguments:  Input_File_Name.[dbf|csv], Data_Owner_User_Id"
            print "Options:    --verbose"
            return
        
        self.err_writer = csv.writer(open(err_file, 'wb'))
        
        if self.file_name.endswith('.csv'):
            rows = self.get_csv_rows(in_file)
        if self.file_name.endswith('.dbf'):
            rows = self.get_dbf_rows(in_file)

        self.data_owner = User.objects.get(pk=self.user_id)
        self.updater = User.objects.get(pk=1)
        
        self.import_event = ImportEvent(file_name=self.file_name)
        self.import_event.save()
        
        print 'Importing %d records' % len(rows)
        for i, row in enumerate(rows):
            self.handle_row(row)
            
            j = i + 1
            if j % 50 == 0:
               print 'Loaded %d...' % j
            self.log_verbose("item %d" % i)
        
        print "Finished data load. "

        print "Calculating new species tree counts... "
        for s in Species.objects.all():
            s.save()
        print "Done."
    
    def log_verbose(self, msg):
        if self.verbose: print msg
    
    def log_error(self, msg, row):
        print "ERROR: %s" % msg
        columns = [row[s] for s in self.headers]
        self.err_writer.writerow(columns)
    
    def check_coords(self, row):
        x = float(row.get('POINT_X', 0))
        y = float(row.get('POINT_Y', 0))

        ok = x and y
        if not ok:
            self.log_error("  Invalid coords", row)
        self.log_verbose("  Passed coordinate check")
        return (ok, x, y)

    def check_species(self, row):
        # locate the species and instanciate the tree instance
        if not row["SCIENTIFIC"]:            
            self.log_verbose("  No species information")
            return (True, None)

        name = row['SCIENTIFIC']
        self.log_verbose("  Looking for species: %s" % name)
        species = Species.objects.filter(scientific_name__iexact=name)

        if species: #species match found
            self.log_verbose("  Found species %r" % species[0])
            return (True, species)
            
        #species data but no match, check it manually
        self.log_error("ERROR:  Unknown species %r" % name, row) 
        return (False, None)

    def check_proximity(self, tree, species, row):
        # check for nearby trees
        collisions = tree.validate_proximity(True, 0)
        
        # if there are no collisions, then proceed as planned
        if not collisions:
            self.log_verbose("  No collisions found")
            return (True, tree)
        self.log_verbose("  Initial proximity test count: %d" % collisions.count())
        
        # exclude collisions from the same file we're working in
        collisions = collisions.exclude(import_event=self.import_event)
        if not collisions:
            self.log_verbose("  All collisions are for from this import file")
            return (True, tree)                
        self.log_verbose("  Secondary proximity test count: %d" % collisions.count())
        
        # if we have multiple collitions, check for same species or unknown species
        # and try to associate with one of them otherwise abort
        if collisions.count() > 1:
            
            # Precedence: single same species, single unknown 
            # return false for all others and log
            if species:                
                same = collisions.filter(species=species[0])            
                if same.count() == 1 and same[0].species == species[0]:
                    self.log_verbose("  Using single nearby tree of same species")
                    return (True, same[0])
            
            unk = collisions.filter(species=None)
                
            if unk.count() == 1:
                self.log_verbose("  Using single nearby tree of unknown species")
                return (True, unk[0])
            
            self.log_error("ERROR:  Proximity test failed (near %d trees)" % collisions.count(), row)
            return (False, None)

        # one nearby match found, use it as base
        tree = collisions[0]
        self.log_verbose("  Found one tree nearby")

        # if neither have a species, then we're done and we need to use
        # the tree we collided with.
        if not tree.species and not species:
            self.log_verbose("  No species info for either record, using %d as base record" % tree.id)
            return (True, tree)

        # if only the new one has a species, update the tree we collided
        # with and then return it
        if not tree.species:
            # we need to update the collision tree with the new species
            tree.set_species(species[0].id, False) # save later
            self.log_verbose("  Species match, using update file species: %s" % species[0])
            return (True, tree)

        # if only the collision tree has a species, we're done.
        if not species or species.count() == 0:
            self.log_verbose("  No species info for import record, using %d as base record" % tree.id)
            return (True, tree)

        # in this case, both had a species. we should check to see if
        # the species are the same.
        if tree.species != species[0]:
            # now that we have a new species, we want to update the
            # collision tree's species and delete all the old status
            # information.
            self.log_verbose("  Species do not match, using update file species: %s" % species[0])
            tree.set_species(species[0].id, False)
            TreeStatus.objects.filter(tree=tree.id).delete()
        return (True, tree) 
    
    def handle_row(self, row):
        self.log_verbose(row)

        # check the physical location
        ok, x, y = self.check_coords(row)
        if not ok: return

        # check the species (if any)
        ok, species = self.check_species(row)
        if not ok: return

        # check the proximity (try to match up with existing trees)
        if (species):
            tree = Tree(species=species[0])
        else:
            tree = Tree()
        tree.geometry = Point(x, y, srid=4326)
        
        ok, tree = self.check_proximity(tree, species, row)
        if not ok: return

        pnt = tree.geometry

        if row.get('ADDRESS') and not tree.address_street:
            tree.address_street = str(row['ADDRESS']).title()
            
        # find the neighborhood, if any
        if not tree.neighborhood:
            n = Neighborhood.objects.filter(geometry__contains=pnt)
            if n: 
                tree.neighborhood = n[0]
                tree.address_city = n[0].city
            else:
                tree.neighborhood = None

        # find the zip code, if any
        if not tree.zipcode:
            z = ZipCode.objects.filter(geometry__contains=pnt)
            if z: 
                tree.zipcode = z[0]
                tree.address_zip = z[0].zip
            else:
                tree.zipcode = None

        # FIXME: get this from the config?
        tree.address_state = 'PA'

        tree.import_event = self.import_event
        tree.last_updated_by = self.updater
        tree.data_owner = self.data_owner
        tree.owner_additional_properties = self.file_name
        if row.get('ID'):
            tree.owner_id = row['ID']
        
        if row.get('PLOTTYPE'):
            for k, v in Choices().get_field_choices('plot'):
                if v == row['PLOTTYPE']:
                    tree.plot_type = v
                    break;
        if row.get('PLOTLENGTH'): 
            tree.plot_length = row['PLOTLENGTH']

        if row.get('PLOTWIDTH'): 
            tree.plot_width = row['PLOTWIDTH']            

        # if powerline is specified, then we want to set our boolean
        # attribute; otherwise leave it alone.
        xyz = row.get('POWERLINE')
        if xyz is None or xyz.strip() == "":
            pass
        elif xyz is True or xyz == "True":
            tree.powerline_conflict_potential = True
        else:
            tree.powerline_conflict_potential = False

        if row.get('OWNER'):
            tree.tree_owner = str(row["OWNER"])

        if row.get('DATEPLANTED'):
            tree.date_planted = str(row['DATEPLANTED'])

        tree.save()

        # add associated objects as needed; skip if no change
        if row.get('DIAMETER') and row['DIAMETER'] != tree.current_dbh: 
            ts = TreeStatus(
                reported_by = tree.last_updated_by,
                value = row['DIAMETER'],
                key = 'dbh',
                tree = tree)                    
            #print ts, ts.value
            ts.save()

        if row.get('HEIGHT') and row['HEIGHT'] != tree.get_height(): 
            ts = TreeStatus(
                reported_by = tree.last_updated_by,
                value = row['HEIGHT'],
                key = 'height',
                tree = tree)
            #print ts, ts.value
            ts.save()

        if row.get('CANOPYHEIGHT') and row['CANOPYHEIGHT'] != tree.get_canopy_height(): 
            ts = TreeStatus(
                reported_by = tree.last_updated_by,
                value = row['CANOPYHEIGHT'],
                key = 'canopy_height',
                tree = tree)
            #print ts, ts.value
            ts.save()

        if row.get('CONDITION') and row['CONDITION'] != tree.get_condition():
            for k, v in Choices().get_field_choices('condition'):
                if v == row['CONDITION']:
                    ts = TreeStatus(
                        reported_by = tree.last_updated_by,
                        value = k,
                        key = 'condition',
                        tree = tree)
                    ts.save()
                    #print ts, ts.value
                    break;
        
        if row.get('CANOPYCONDITION') and row['CANOPYCONDITION'] != tree.get_canopy_condition():
            for k, v in Choices().get_field_choices('canopy_condition'):
                if v == row['CANOPYCONDITION']:
                    ts = TreeStatus(
                        reported_by = tree.last_updated_by,
                        value = k,
                        key = 'canopy_condition',
                        tree = tree)
                    ts.save()
                    #print ts, ts.value
                    break;

        # rerun validation tests and store results
        tree.validate_all()
