from os.path import dirname
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from UrbanForestMap.treemap.models import Species, Tree, Neighborhood, ZipCode, TreeStatus, Choices

class Command(BaseCommand):
    args = '<input_file_name, data_owner_id>'
    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose debug text'),
    )

    
    def handle(self, *args, **options):
    
        try:    
            in_file = dirname(__file__) + "\\" + args[0]
            err_file = dirname(__file__) + "\\" + args[0] + ".err"
            verbose = options.get('verbose')
            user_id = args[1]
        except:
            #TODO: add usage
            print "args error"
            return
        
        if args[0].endswith('.csv'):
            print 'Not supported yet'
            return

        self.stdout.write('Opening input file: %s \n' % in_file)
        reader = dbf.Dbf(in_file)
        err_writer = csv.writer(open(err_file, 'wb'))
        

        header_row = []
        
        self.stdout.write('Importing ' + reader.recordCount.__str__() + ' records... \n')
        
        last_updated_by = User.objects.get(pk=1)
        data_owner = User.objects.get(pk=user_id)
        
        err_writer.writerow(reader.fieldNames)
        
        for row in reader:
        
            if verbose:
                print row
            # coord fields here but blank or 0,0
            if not row['POINT_X'] or row['POINT_X'] == 0:
                err_writer.writerow(row.asList())
                continue
                       
            # locate the species and instanciate the tree instance
            if row["SCIENTIFIC"]:
                if verbose:
                    print "  Looking for species: " + row['SCIENTIFIC']
                species = Species.objects.filter(scientific_name__iexact=row['SCIENTIFIC'])
                if species.count() > 0: #species match found
                    tree = Tree(species=species[0])
                    if verbose:
                        print "  Found species " + species[0].__str__()
                else:
                    if verbose:
                        print "ERROR:  Species match not found"
                    err_writer.writerow(row.asList()) #species data but no match, check it manually
                    continue
            else:
                species = None
                tree = Tree()

            # add tree fields
            pnt = Point(float(row['POINT_X']),float(row['POINT_Y']),srid=4326)
            tree.geometry = pnt
            
            # check for nearby trees
            proximity_test = tree.validate_proximity(True, 0)
            if proximity_test:
                if verbose:
                    print "  Proximity test count: " + proximity_test.count()
                if proximity_test.count() > 1: # more than one tree nearby, so manually correct later
                    err_writer.writerow(row.asList())
                    if verbose:
                        print "ERROR:  Proximity test failed with a count of " + proximity_test.count().__str__()
                    continue
                # one nearby match found, use it as base
                tree = proximity_test[0]
                if verbose:
                    print "  Found one tree nearby, using " + tree.id.__str__() + " as base record"
                
                if tree.species:
                    if verbose:
                        print "  Found species on base record: " + tree.species.__str__()
                    if species and species.count() > 0: # both records have species, reconcile
                        if not tree.species == species[0]: # different species = update
                            tree.set_species(species[0].id, False)
                            if verbose:
                                print "  No species on base tree, clearing old status objects"
                                print "  Deleted " + TreeStatus.objects.filter(tree=tree.id).count().__str__() + " old status objects"
                            TreeStatus.objects.filter(tree=tree.id).delete()                            
                            
                        else:       # same species = same tree
                            pass
                else:
                    if species and species.count() > 0: # only update has species so use it
                        tree.set_species(species[0].id, False) # save later
                        if verbose:
                            print "  Species match, using update file species: " + species[0].__str__()
                
            # don't query if the tree already has one
            if not tree.neighborhood:
                n = Neighborhood.objects.filter(geometry__contains=pnt)
                if n: 
                    tree.neighborhood = n[0]
                else: tree.neighborhood = None
            if not tree.zipcode:
                z = ZipCode.objects.filter(geometry__contains=pnt)
                if z: 
                    tree.zipcode = z[0]
                    tree.address_zip = z[0].zip
                else: tree.zipcode = None
            
            ##print "old street: " + tree.address_street.__str__()
            tree.address_city = 'Philadelphia'
            if 'ADDRESS' in reader.fieldNames and row['ADDRESS'] and not tree.address_street:
                tree.address_street = row['ADDRESS'].__str__().title()
                ##print "new street: " + tree.address_street.__str__()
            tree.address_state = 'PA'
            tree.last_updated_by = last_updated_by
            tree.last_updated = datetime.now()
            tree.data_owner = data_owner
            if 'PLOTTYPE' in reader.fieldNames and row['PLOTTYPE']:
                for k,v in Choices().get_field_choices('plot'):
                    if v == row['PLOTTYPE']:
                        ##print "plot type"
                        tree.plot_type = v
                        break;
            if 'PLOTLENGTH' in reader.fieldNames and row['PLOTLENGTH']: 
                    tree.plot_length = row['PLOTLENGTH']
            if 'PLOTWIDTH' in reader.fieldNames and row['PLOTWIDTH']: 
                    tree.plot_width = row['PLOTWIDTH']            
            
            if 'POWERLINE' in reader.fieldNames and row['POWERLINE'] :
                if not row['POWERLINE'] == True: #everything other than True is False
                    tree.powerline_conflict_potential = False
                else: 
                    tree.powerline_conflict_potential = True
            
            if 'COMMUNITY' in reader.fieldNames and row['COMMUNITY']:
                if not tree.owner_additional_properties:
                    tree.owner_additional_properties = " Community: " + row["COMMUNITY"].__str__()
                else:
                    tree.owner_additional_properties += " Community: " + row["COMMUNITY"].__str__()
            
            if 'OWNER' in reader.fieldNames and row['OWNER']:
                tree.tree_owner = row["OWNER"].__str__()
            
            if 'DATEPLANTED' in reader.fieldNames and row['DATEPLANTED']:
                tree.date_planted = row['DATEPLANTED']
                        
            tree.save()
            
            # add associated objects as needed; skip if no change
            if 'DIAMETER' in reader.fieldNames and row['DIAMETER'] and not row['DIAMETER'] == tree.current_dbh: 
                ts = TreeStatus(
                    reported_by = tree.last_updated_by,
                    value = row['DIAMETER'],
                    key = 'dbh',
                    tree = tree)                    
                #print ts, ts.value
                ts.save()
                
            if 'HEIGHT' in reader.fieldNames and row['HEIGHT'] and not row['HEIGHT'] == tree.get_height(): 
                ts = TreeStatus(
                    reported_by = tree.last_updated_by,
                    value = row['HEIGHT'],
                    key = 'height',
                    tree = tree)
                #print ts, ts.value
                ts.save()
                
            if 'CANOPYHEIGHT' in reader.fieldNames and row['CANOPYHEIGHT'] and not row['CANOPYHEIGHT'] == tree.get_canopy_height(): 
                ts = TreeStatus(
                    reported_by = tree.last_updated_by,
                    value = row['CANOPYHEIGHT'],
                    key = 'canopy_height',
                    tree = tree)
                #print ts, ts.value
                ts.save()
            
            if 'CONDITION' in reader.fieldNames and row['CONDITION']:
                for k,v in Choices().get_field_choices('condition'):
                    if v == row['CONDITION']:
                        ts = TreeStatus(
                            reported_by = tree.last_updated_by,
                            value = k,
                            key = 'condition',
                            tree = tree)
                        ts.save()
                        #print ts, ts.value
                        break;
            if 'CANOPYCONDITION' in reader.fieldNames and row['CANOPYCONDITION']:
                for k,v in Choices().get_field_choices('canopy_condition'):
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
            
            human_index = row.index +1
            if human_index % 100 == 0:
               self.stdout.write('Loaded %s... \n' % human_index)

            if verbose:
                print human_index
        
        print "Finished data load. "
        reader.close()
        
        print "Calculating new species tree counts... "
        for s in Species.objects.all():
            s.save()
        print "Done."