from os.path import dirname
import csv
from datetime import datetime
from dbfpy import dbf
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.auth.models import User
from treemap.models import Species, Tree, Plot, Neighborhood, ZipCode, TreeFlags, ImportEvent

# Change explicit value of plot.address_street (see 'TODO' below) as desired.
# Load CHOICES from your implementation-specific file (e.g. "from choices_SanDiego import *")
from choices import CHOICES as choices

class Command(BaseCommand):
    args = '<input_file_name, data_owner_id, base_srid, read_only>'
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

    def handle(self, *args, **options):
        self.wrote_headers = False
        try:
            self.file_name = args[0]
            in_file = self.file_name
            err_file = in_file + ".err"
            self.verbose = options.get('verbose')
            self.user_id = args[1]
            if len(args) > 2:
                self.base_srid = int(args[2])
                self.tf = CoordTransform(SpatialReference(self.base_srid), SpatialReference(4326))
                print "Using transformation object: %s" % self.tf
            else:
                self.base_srid = 4326
            if len(args) > 3:
                self.readonly = bool(args[3])
                print "Setting readonly flag to %s" % self.readonly
            else:
                self.readonly = False
        except:
            print "Arguments:  Input_File_Name.[dbf|csv] Data_Owner_User_Id (Optional: Base_SRID ReadOnly-bool)"
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
        self.write_headers_if_needed()
        self.err_writer.writerow(columns)

    def check_coords(self, row):
        try:
            x = float(row.get('POINT_X', 0))
            y = float(row.get('POINT_Y', 0))
        except:
            self.log_error("  Invalid coords, might not be numbers", row)
            return (False, 0, 0)

        ok = x and y
        if not ok:
            self.log_error("  Invalid coords", row)
        self.log_verbose("  Passed coordinate check")
        return (ok, x, y)

    def check_species(self, row):
        # locate the species and instanciate the tree instance
        if not row.get('SCIENTIFIC') and not row.get('GENUS'):
            self.log_verbose("  No species information")
            return (True, None)

        if row.get('SCIENTIFIC'):
            name = str(row['SCIENTIFIC']).strip()
            species_obj = Species.objects.filter(scientific_name__iexact=name)
            self.log_verbose("  Looking for species: %s" % name)
        else:
            genus = str(row['GENUS']).strip()
            species_field = ''
            cultivar = ''
            gender = ''
            name = genus
            if row.get('SPECIES'):
                species_field = str(row['SPECIES']).strip()
                name = name + " " + species_field
            if row.get('CULTIVAR'):
                cultivar = str(row['CULTIVAR']).strip()
                name = name + " " + cultivar
            if row.get('GENDER'):
                gender = str(row['GENDER']).strip()
                name = name + " " + gender
            species_obj = Species.objects.filter(genus__iexact=genus,species__iexact=species_field,cultivar_name__iexact=cultivar,gender__iexact=gender)
            self.log_verbose("  Looking for species: %s" % name)


        if species_obj: #species match found
            self.log_verbose("  Found species %r" % species_obj[0])
            return (True, species_obj)

        #species data but no match, check it manually
        self.log_error("ERROR:  Unknown species %r" % name, row)
        return (False, None)

    def check_tree_info(self, row):
        tree_info = False
        fields = ['STEWARD', 'SPONSOR', 'DATEPLANTED', 'DIAMETER', 'HEIGHT', 'CANOPYHEIGHT',
                  'CONDITION', 'CANOPYCONDITION', 'PROJECT_1', 'PROJECT_2', 'PROJECT_3', 'OWNER']

        for f in fields:
            # field exists and there's something in it
            if row.get(f) and str(row[f]).strip():
                tree_info = True
                self.log_verbose('  Found tree data in field %s, creating a tree' % f)
                break

        return tree_info

    def check_proximity(self, plot, tree, species, row):
        # check for nearby plots
        collisions = plot.validate_proximity(True, 0)

        # if there are no collisions, then proceed as planned
        if not collisions:
            self.log_verbose("  No collisions found")
            return (True, plot, tree)
        self.log_verbose("  Initial proximity test count: %d" % collisions.count())

        # exclude collisions from the same file we're working in
        collisions = collisions.exclude(import_event=self.import_event)
        if not collisions:
            self.log_verbose("  All collisions are from this import file")
            return (True, plot, tree)
        self.log_verbose("  Secondary proximity test count: %d" % collisions.count())

        # if we have multiple collitions, check for same species or unknown species
        # and try to associate with one of them otherwise abort
        if collisions.count() > 1:
            # get existing trees for the plots that we collided with
            tree_ids = []
            for c in collisions:
                if c.current_tree():
                    tree_ids.append(c.current_tree().id)

            trees = Tree.objects.filter(id__in=tree_ids)

            # Precedence: single same species, single unknown
            # return false for all others and log
            if species:
                same = trees.filter(species=species[0])
                if same.count() == 1 and same[0].species == species[0]:
                    self.log_verbose("  Using single nearby plot with tree of same species")
                    return (True, c, same[0])

            unk = trees.filter(species=None)

            if unk.count() == 1:
                self.log_verbose("  Using single nearby plot with tree of unknown species")
                return (True, c,  unk[0])

            self.log_error("ERROR:  Proximity test failed (near %d plots)" % collisions.count(), row)
            return (False, None, None)

        # one nearby match found, use it as base
        plot = collisions[0]
        plot_tree = plot.current_tree()
        self.log_verbose("  Found one tree nearby")

        # if the nearby plot doesn't have a tree, don't bother doing species matching
        if not plot_tree:
            self.log_verbose("  No tree found for plot, using %d as base plot record" % plot.id)
            return (True, plot, tree)

        # if neither have a species, then we're done and we need to use
        # the tree we collided with.
        if not plot_tree.species and not species:
            self.log_verbose("  No species info for either record, using %d as base tree record" % plot_tree.id)
            return (True, plot, plot_tree)

        # if only the new one has a species, update the tree we collided
        # with and then return it
        if not plot_tree.species:
            # we need to update the collision tree with the new species
            plot_tree.set_species(species[0].id, False) # save later
            self.log_verbose("  Species match, using update file species: %s" % species[0])
            return (True, plot, plot_tree)

        # if only the collision tree has a species, we're done.
        if not species or species.count() == 0:
            self.log_verbose("  No species info for import record, using %d as base record" % plot_tree.id)
            return (True, plot, plot_tree)

        # in this case, both had a species. we should check to see if
        # the species are the same.
        if plot_tree.species != species[0]:
            # now that we have a new species, we want to update the
            # collision tree's species and delete all the old status
            # information.
            self.log_verbose("  Species do not match, using update file species: %s" % species[0])
            plot_tree.set_species(species[0].id, False)
            plot_tree.dbh = None
            plot_tree.height = None
            plot_tree.canopy_height = None
            plot_tree.condition = None
            plot_tree.canopy_condition = None
        return (True, plot, plot_tree)

    def handle_row(self, row):
        self.log_verbose(row)

        # check the physical location
        ok, x, y = self.check_coords(row)
        if not ok: return

        plot = Plot()

        try:
            if self.base_srid != 4326:
                geom = Point(x, y, srid=self.base_srid)
                geom.transform(self.tf)
                self.log_verbose(geom)
                plot.geometry = geom
            else:
                plot.geometry = Point(x, y, srid=4326)
        except:
            self.log_error("ERROR: Geometry failed to transform", row)
            return

        # check the species (if any)
        ok, species = self.check_species(row)
        if not ok: return

        # check for tree info, should we create a tree or just a plot
        if species or self.check_tree_info(row):
            tree = Tree(plot=plot)
        else:
            tree = None

        if tree and species:
            tree.species = species[0]


        # check the proximity (try to match up with existing trees)
        # this may return a different plot/tree than created just above,
        # so don't set anything else on either until after this point
        ok, plot, tree = self.check_proximity(plot, tree, species, row)
        if not ok: return


        if row.get('ADDRESS') and not plot.address_street:
            plot.address_street = str(row['ADDRESS']).title()
            plot.geocoded_address = str(row['ADDRESS']).title()

        if not plot.geocoded_address:
            plot.geocoded_address = ""

        # FIXME: get this from the config?
        plot.address_state = 'CA'
        plot.import_event = self.import_event
        plot.last_updated_by = self.updater
        plot.data_owner = self.data_owner
        plot.readonly = self.readonly

        if row.get('PLOTTYPE'):
            for k, v in choices['plot_types']:
                if v == row['PLOTTYPE']:
                    plot.type = k
                    break;

        if row.get('PLOTLENGTH'):
            plot.length = row['PLOTLENGTH']

        if row.get('PLOTWIDTH'):
            plot.width = row['PLOTWIDTH']

        if row.get('ID'):
            plot.owner_orig_id = row['ID']

        if row.get('ORIGID'):
            plot.owner_additional_properties = "ORIGID=" + str(row['ORIGID'])

        if row.get('OWNER_ADDITIONAL_PROPERTIES'):
            plot.owner_additional_properties = str(plot.owner_additional_properties) + " " + str(row['OWNER_ADDITIONAL_PROPERTIES'])

        if row.get('OWNER_ADDITIONAL_ID'):
            plot.owner_additional_id = str(row['OWNER_ADDITIONAL_ID'])

        if row.get('POWERLINE'):
            for k, v in choices['powerlines']:
                if v == row['POWERLINE']:
                    plot.powerline_conflict_potential = k
                    break;

        sidewalk_damage = row.get('SIDEWALK')
        if sidewalk_damage is None or sidewalk_damage.strip() == "":
            pass
        elif sidewalk_damage is True or sidewalk_damage.lower() == "true" or sidewalk_damage.lower() == 'yes':
            plot.sidewalk_damage = 2
        else:
            plot.sidewalk_damage = 1

        plot.quick_save()

        pnt = plot.geometry
        n = Neighborhood.objects.filter(geometry__contains=pnt)
        z = ZipCode.objects.filter(geometry__contains=pnt)

        plot.neighborhoods = ""
        plot.neighborhood.clear()
        plot.zipcode = None

        if n:
            for nhood in n:
                if nhood:
                    plot.neighborhoods = plot.neighborhoods + " " + nhood.id.__str__()
                    plot.neighborhood.add(nhood)

        if z: plot.zipcode = z[0]

        plot.quick_save()

        if tree:
            tree.plot = plot
            tree.readonly = self.readonly
            tree.import_event = self.import_event
            tree.last_updated_by = self.updater

            if row.get('OWNER'):
                tree.tree_owner = str(row["OWNER"])

            if row.get('STEWARD'):
                tree.steward_name = str(row["STEWARD"])

            if row.get('SPONSOR'):
                tree.sponsor = str(row["SPONSOR"])

            if row.get('DATEPLANTED'):
                date_string = str(row['DATEPLANTED'])
                try:
                    date = datetime.strptime(date_string, "%m/%d/%Y")
                except:
                    pass
                try:
                    date = datetime.strptime(date_string, "%Y/%m/%d")
                except:
                    pass
                if not date:
                    raise ValueError("Date strings must be in mm/dd/yyyy or yyyy/mm/dd format")

                tree.date_planted = date.strftime("%Y-%m-%d")

            if row.get('DIAMETER'):
                tree.dbh = float(row['DIAMETER'])

            if row.get('HEIGHT'):
                tree.height = float(row['HEIGHT'])

            if row.get('CANOPYHEIGHT'):
                tree.canopy_height = float(row['CANOPYHEIGHT'])

            if row.get('CONDITION'):
                for k, v in choices['conditions']:
                    if v == row['CONDITION']:
                        tree.condition = k
                        break;

            if row.get('CANOPYCONDITION'):
                for k, v in choices['canopy_conditions']:
                    if v == row['CANOPYCONDITION']:
                        tree.canopy_condition = k
                        break;

            tree.quick_save()

            if row.get('PROJECT_1'):
                for k, v in Choices().get_field_choices('local'):
                    if v == row['PROJECT_1']:
                        local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                        local.save()
                        break;
            if row.get('PROJECT_2'):
                for k, v in Choices().get_field_choices('local'):
                    if v == row['PROJECT_2']:
                        local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                        local.save()
                        break;
            if row.get('PROJECT_3'):
                for k, v in Choices().get_field_choices('local'):
                    if v == row['PROJECT_3']:
                        local = TreeFlags(key=k,tree=tree,reported_by=self.updater)
                        local.save()
                        break;

            # rerun validation tests and store results
            tree.validate_all()
