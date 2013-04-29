import csv
import json

from importer.models import TreeImportEvent, TreeImportRow

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
