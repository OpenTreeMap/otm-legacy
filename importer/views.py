import csv
import json

from treemap.models import Species, Neighborhood, Plot

from importer.models import TreeImportEvent, TreeImportRow
from django.contrib.gis.geos import Point


class Fields:
    # X/Y are required
    POINT_X = 'point x'
    POINT_Y = 'point y'

    # Plot Fields
    ADDRESS = 'address'
    PLOT_WIDTH = 'plot width'
    PLOT_LENGTH = 'plot length'

    READ_ONLY = 'read only'
    OPENTREEMAP_ID_NUMBER = 'opentreemap id number'
    ORIG_ID_NUMBER = 'original id number'

    TREE_PRESENT = 'tree present'

    # Choice fields
    PLOT_TYPE = 'plot type'
    POWERLINE_CONFLICT = 'powerline conflict'
    SIDEWALK = 'sidewalk'

    # Tree Fields
    GENUS = 'genus'
    SPECIES = 'species'
    CULTIVAR = 'cultivar'
    SCI_NAME = 'other part of scientific name'
    DIAMETER = 'diameter'
    CANOPY_HEIGHT = 'canopy height'
    DATE_PLANTED = 'date planted'
    DATA_SOURCE = 'data source'
    OWNER = 'tree owner'
    SPONSOR = 'tree sponsor'
    STEWARD = 'tree steward'
    NOTES = 'notes'
    URL = 'tree url'

    # Choice Fields
    TREE_CONDITION = 'condition'
    CANOPY_CONDITION = 'canopy condition'
    ACTIONS = 'actions'
    PESTS = 'pests and diseases'
    LOCAL_PROJECTS = 'local projects'

    ALL = { POINT_X, POINT_Y, ADDRESS, PLOT_WIDTH,
            PLOT_LENGTH, READ_ONLY, OPENTREEMAP_ID_NUMBER,
            TREE_PRESENT, PLOT_TYPE, POWERLINE_CONFLICT,
            SIDEWALK, GENUS, SPECIES, CULTIVAR,
            SCI_NAME, DIAMETER, ORIG_ID_NUMBER,
            CANOPY_HEIGHT, DATE_PLANTED, TREE_CONDITION,
            CANOPY_CONDITION, ACTIONS, PESTS,
            LOCAL_PROJECTS, URL, NOTES, OWNER,
            SPONSOR, STEWARD, DATA_SOURCE }

class Errors:
    """ 3 tuples (error id, error descr, fatal) """
    EMPTY_FILE = (1, 'No rows found', True)
    MISSING_POINTS = (2, 'You must specify a "%s" and "%s" field' %\
                      (Fields.POINT_X, Fields.POINT_Y), True)

    UNMATCHED_FIELDS = (3, "Some fields in the uploaded dataset"\
                        "didn't match the template", False)

    INVALID_GEOM = (10, 'Longitude must be between -180 and 180 and'\
                    'latitude must be betwen -90 and 90', True)

    GEOM_OUT_OF_BOUNDS = (11, 'Geometry must be in a neighborhood', True)

    INVALID_SPECIES = (20, 'Could not find matching species', True)

    INVALID_OTM_ID = (30, 'The given Open Tree Map ID does not exist '\
                      'in the system. This ID is automatically generated '\
                      'by Open Tree Map and should only be used for '\
                      'updating existing records', True)

    FLOAT_ERROR = (40, 'Not formatted as a number', True)
    INT_ERROR = (41, 'Not formatted as an integer', True)

def lowerkeys(h):
    h2 = {}
    for (k,v) in h.iteritems():
        h2[k.lower()] = v

    return h2

def create_rows_for_event(importevent, tmp_path):
    rows = []
    with open(tmp_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rows.append(
                TreeImportRow.objects.create(
                    data=json.dumps(lowerkeys(row)),
                    import_event=importevent))

    return rows

def validate_main_file(importevent):
    """
    Make sure the imported file has rows and valid columns
    """
    if importevent.treeimportrow_set.count() == 0:
        importevent.append_error(Errors.EMPTY_FILE)

        # This is a fatal error. We need to have at least
        # one row to get header info
        importevent.save()
        return False

    errors = False
    datastr = importevent.treeimportrow_set.all()[0].data
    fields = set(json.loads(datastr).keys())

    # Point x/y fields are required
    if Fields.POINT_X not in fields or Fields.POINT_Y not in fields:
        errors = True
        importevent.append_error(Errors.MISSING_POINTS)

    # It is a warning if there are extra input fields
    rem = fields - Fields.ALL
    if len(rem) > 0:
        errors = True
        importevent.append_error(Errors.UNMATCHED_FIELDS, list(rem))

    if errors:
        importevent.save()

    return not errors

def get_species_for_row(importrow):
    """
    Validate and return a species for a given input row

    if no species was specifed at all this method returns:
       None
    if a species was specified and found this method returns that species
    if a species was specified and *not* found this method:
       Adds an error to the importrow
       returns False
    """
    genus = importrow.datadict.get(Fields.GENUS,'')
    species = importrow.datadict.get(Fields.SPECIES,'')
    cultivar = importrow.datadict.get(Fields.CULTIVAR,'')

    if genus == '' and species == '' and cultivar == '':
        return None # Don't create a species at all
    else:
        matching_species = Species.objects\
                                  .filter(genus__iexact=genus)\
                                  .filter(species__iexact=species)\
                                  .filter(cultivar_name__iexact=cultivar)

        if matching_species:
            return matching_species[0]
        else:
            importrow.append_error(Errors.INVALID_SPECIES,
                                   ' '.join([genus,species,cultivar]))
            return False

def safe_float(importrow, fld):
    try:
        return float(importrow.datadict[fld])
    except:
        importrow.append_error(Errors.FLOAT_ERROR, importrow.datadict[fld])
        return False

def safe_int(importrow, fld):
    try:
        return int(importrow.datadict[fld])
    except:
        importrow.append_error(Errors.INT_ERROR, importrow.datadict[fld])
        return False

def validate_geom(importrow):
    x = safe_float(importrow, Fields.POINT_X)
    y = safe_float(importrow, Fields.POINT_Y)

    # Check if number was malformed
    if x is False or y is False:
        return False

    # Simple validation
    # longitude must be between -180 and 180
    # latitude must be betwen -90 and 90
    if abs(x) > 180 or abs(y) > 90:
        importrow.append_error(Errors.INVALID_GEOM)
        return False

    p = Point(x,y)

    if Neighborhood.objects.filter(geometry__contains=p).exists():
        return p
    else:
        importrow.append_error(Errors.GEOM_OUT_OF_BOUNDS)
        return False

def validate_otm_id(importrow):
    if Fields.OPENTREEMAP_ID_NUMBER in importrow.datadict:
        oid = safe_int(importrow, Fields.OPENTREEMAP_ID_NUMBER)

        # Check for invalid number
        if oid is False:
            return False

        has_plot = Plot.objects.filter(
            pk=oid).exists()

        if has_plot:
            return oid
        else:
            importrow.append_error(Errors.INVALID_OTM_ID, oid)
            return False
    else:
        return True

def get_plot_from_row(importrow):
    """ Returns a Plot object if things are looking good,
    otherwise returns 'False'

    This method mutates the errors on the import row
    """

    # Validations append errors directly to importrow
    oid = validate_otm_id(importrow)
    pt = validate_geom(importrow)
    species = get_species_for_row(importrow)

    # If any errors were added that are marked as fatal,
    # save and abort here
    if importrow.errors:
        for err in json.loads(importrow.errors):
            if err['fatal']:
                importrow.save()
                return False
