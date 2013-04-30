import csv
import json
from datetime import datetime

from django.http import HttpResponse
from django.conf import settings

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.auth.models import User

from treemap.models import Species, Neighborhood, Plot

from importer.models import TreeImportEvent, TreeImportRow

class Fields:
    # X/Y are required
    POINT_X = 'point x'
    POINT_Y = 'point y'

    # This is a pseudo field which is filled in
    # when data is cleaned and contains a GEOS
    # point object
    POINT = 'calc__point'

    # This is a pseudo field which is filled in
    # when data is cleaned and may contain a
    # OTM Species object, if the species was
    # matched
    SPECIES_OBJECT = 'calc__species_object'

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
    TREE_HEIGHT = 'tree height'
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

    CHOICE_MAP = {
        PLOT_TYPE: 'plot_types',
        POWERLINE_CONFLICT: 'powerlines',
        SIDEWALK: 'sidewalks',
        TREE_CONDITION: 'conditions',
        CANOPY_CONDITION: 'tree_conditions',
        ACTIONS: 'actions',
        PESTS: 'pests',
        LOCAL_PROJECTS: 'projects'
    }

    ALL = { POINT_X, POINT_Y, ADDRESS, PLOT_WIDTH,
            PLOT_LENGTH, READ_ONLY, OPENTREEMAP_ID_NUMBER,
            TREE_PRESENT, PLOT_TYPE, POWERLINE_CONFLICT,
            SIDEWALK, GENUS, SPECIES, CULTIVAR,
            SCI_NAME, DIAMETER, ORIG_ID_NUMBER,
            CANOPY_HEIGHT, DATE_PLANTED, TREE_CONDITION,
            CANOPY_CONDITION, ACTIONS, PESTS,
            LOCAL_PROJECTS, URL, NOTES, OWNER,
            SPONSOR, STEWARD, DATA_SOURCE, TREE_HEIGHT }

class Errors:
    """ 3 tuples (error id, error descr, fatal) """
    EMPTY_FILE = (1, 'No rows found', True)
    MISSING_POINTS = (2, 'You must specify a "%s" and "%s" field' %\
                      (Fields.POINT_X, Fields.POINT_Y), True)

    UNMATCHED_FIELDS = (3, "Some fields in the uploaded dataset "\
                        "didn't match the template", False)

    INVALID_GEOM = (10, 'Longitude must be between -180 and 180 and '\
                    'latitude must be betwen -90 and 90', True)

    GEOM_OUT_OF_BOUNDS = (11, 'Geometry must be in a neighborhood', True)

    INVALID_SPECIES = (20, 'Could not find matching species', True)

    INVALID_OTM_ID = (30, 'The given Open Tree Map ID does not exist '\
                      'in the system. This ID is automatically generated '\
                      'by Open Tree Map and should only be used for '\
                      'updating existing records', True)

    FLOAT_ERROR = (40, 'Not formatted as a number', True)
    POS_FLOAT_ERROR = (41, 'Not formatted as a positive number', True)
    INT_ERROR = (42, 'Not formatted as an integer', True)
    POS_INT_ERROR = (43, 'Not formatted as a positive integer', True)
    BOOL_ERROR = (44, 'Not formatted as a boolean', True)
    STRING_TOO_LONG = (45, 'Strings must be less than 255 characters', True)
    INVALID_DATE = (46, 'Invalid date (must by YYYY-MM-DD', True)

    INVALID_CHOICE = (50, 'These fields must contain a choice value', True)

    NEARBY_TREES = (1050, 'There are already trees very close to this one', False)

    SPECIES_DBH_TOO_HIGH = (1060,
                            'The diameter is too large for this species',
                            False)

    SPECIES_HEIGHT_TOO_HIGH = (1061,
                               'The height is too large for this species',
                               False)

def lowerkeys(h):
    h2 = {}
    for (k,v) in h.iteritems():
        h2[k.lower()] = v

    return h2


def process_csv(request):
    owner = User.objects.all()[0]
    ie = TreeImportEvent(file_name=request.REQUEST['name'],
                         owner=owner)
    ie.save()

    rows = create_rows_for_event(ie, request.FILES.values()[0])
    filevalid = validate_main_file(ie)

    if filevalid:
        for row in rows:
            validate_row(row)

    return HttpResponse(
        json.dumps({'id': ie.pk}),
        content_type = 'application/json')

def process_status(request, import_id):
    ie = TreeImportEvent.objects.get(pk=import_id)

    resp = None
    if ie.errors:
        resp = {'status': 'file_error',
                'errors': json.loads(ie.errors)}
    else:
        errors = []
        for row in ie.treeimportrow_set.all():
            if row.errors:
                errors.append((row.idx, json.loads(row.errors)))

        if len(errors) > 0:
            resp = {'status': 'row_error',
                    'errors': dict(errors)}

    if resp is None:
        resp = {'status': 'success',
                'rows': ie.treeimportrow_set.count()}

    return HttpResponse(
        json.dumps(resp),
        content_type = 'application/json')

def create_rows_for_event(importevent, csvfile):
    rows = []
    reader = csv.DictReader(csvfile)

    idx = 0
    for row in reader:
        rows.append(
            TreeImportRow.objects.create(
                data=json.dumps(lowerkeys(row)),
                import_event=importevent, idx=idx))

        idx += 1

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

def validate_species(importrow):
    genus = importrow.datadict.get(Fields.GENUS,'')
    species = importrow.datadict.get(Fields.SPECIES,'')
    cultivar = importrow.datadict.get(Fields.CULTIVAR,'')

    if genus != '' or species != '' or cultivar != '':
        matching_species = Species.objects\
                                  .filter(genus__iexact=genus)\
                                  .filter(species__iexact=species)\
                                  .filter(cultivar_name__iexact=cultivar)

        if len(matching_species) == 1:
            importrow.cleaned[Fields.SPECIES_OBJECT] = matching_species[0]
        else:
            importrow.append_error(Errors.INVALID_SPECIES,
                                   ' '.join([genus,species,cultivar]).strip())
            return False

    return True

def safe_float(importrow, fld):
    try:
        return float(importrow.datadict[fld])
    except:
        importrow.append_error(Errors.FLOAT_ERROR, fld)
        return False

def safe_bool(importrow, fld):
    """ Returns a tuple of (success, bool value) """
    v = importrow.datadict.get(fld, '').lower()

    if v == 'true':
        return (True,True)
    elif v == 'false':
        return (True,False)
    else:
        importrow.append_error(Errors.BOOL_ERROR, fld)
        return (False,None)


def safe_int(importrow, fld):
    try:
        return int(importrow.datadict[fld])
    except:
        importrow.append_error(Errors.INT_ERROR, fld)
        return False

def safe_pos_int(importrow, fld):
    i = safe_int(importrow, fld)

    if i is False:
        return False
    elif i < 0:
        importrow.append_error(Errors.POS_INT_ERROR, fld)
        return False
    else:
        return i

def safe_pos_float(importrow, fld):
    i = safe_float(importrow, fld)

    if i is False:
        return False
    elif i < 0:
        importrow.append_error(Errors.POS_FLOAT_ERROR, fld)
        return False
    else:
        return i

def validate_geom(importrow):
    x = importrow.cleaned.get(Fields.POINT_X, None)
    y = importrow.cleaned.get(Fields.POINT_Y, None)

    # Note, this shouldn't really happen since main
    # file validation will fail, but butter safe than sorry
    if x is None or y is None:
        importrow.append_error(Errors.MISSING_POINTS)
        return False

    # Simple validation
    # longitude must be between -180 and 180
    # latitude must be betwen -90 and 90
    if abs(x) > 180 or abs(y) > 90:
        importrow.append_error(Errors.INVALID_GEOM)
        return False

    p = Point(x,y)

    if Neighborhood.objects.filter(geometry__contains=p).exists():
        importrow.cleaned[Fields.POINT] = p
        return True
    else:
        importrow.append_error(Errors.GEOM_OUT_OF_BOUNDS)
        return False

def validate_otm_id(importrow):
    oid = importrow.cleaned.get(Fields.OPENTREEMAP_ID_NUMBER, None)
    if oid:
        has_plot = Plot.objects.filter(
            pk=oid).exists()

        if not has_plot:
            importrow.append_error(Errors.INVALID_OTM_ID, oid)
            return False

    return True

def validate_proximity(importrow, point):
    nearby = Plot.objects\
                 .filter(present=True,
                         geometry__distance_lte=(point, D(ft=10.0)))\
                 .distance(point)\
                 .order_by('distance')[:5]

    if len(nearby) > 0:
        importrow.append_error(Errors.NEARBY_TREES, [p.pk for p in nearby])
        return False
    else:
        return True

def validate_species_max(importrow, field, max_val, err):
    inputval = importrow.cleaned.get(field, None)
    if inputval:
        if max_val and inputval > max_val:
            importrow.append_error(err, max_val)
            return False

    return True


def validate_species_dbh_max(importrow, species):
    return validate_species_max(
        importrow, Fields.DIAMETER,
        species.v_max_dbh, Errors.SPECIES_DBH_TOO_HIGH)

def validate_species_height_max(importrow, species):
    return validate_species_max(
        importrow, Fields.TREE_HEIGHT,
        species.v_max_height, Errors.SPECIES_HEIGHT_TOO_HIGH)

def validate_numeric_fields(importrow):
    def cleanup(fields, fn):
        errors = False
        for f in fields:
            if f in importrow.datadict and importrow.datadict[f]:
                maybe_num = fn(importrow, f)

                if maybe_num is False:
                    errors = True
                else:
                    importrow.cleaned[f] = maybe_num

        return errors

    pfloat_ok = cleanup([Fields.PLOT_WIDTH, Fields.PLOT_LENGTH,
                             Fields.DIAMETER, Fields.TREE_HEIGHT,
                             Fields.CANOPY_HEIGHT], safe_pos_float)

    float_ok = cleanup([Fields.POINT_X, Fields.POINT_Y],
                           safe_float)

    int_ok = cleanup([Fields.OPENTREEMAP_ID_NUMBER],
                         safe_pos_int)

    return pfloat_ok and float_ok and int_ok

def validate_boolean_fields(importrow):
    errors = False
    for f in [Fields.READ_ONLY, Fields.TREE_PRESENT]:
        if f in importrow.datadict:
            success, v = safe_bool(importrow, f)
            if success:
                importrow.cleaned[f] = v
            else:
                errors = True

    return errors

def validate_choice_fields(importrow):
    errors = False
    for field,choice_key in Fields.CHOICE_MAP.iteritems():
        if field in importrow.datadict:
            value = importrow.datadict[field]
            choices = { value for (id,value) in
                       settings.CHOICES[choice_key] }

            if value in choices:
                importrow.cleaned[field] = value
            else:
                errors = True
                importrow.append_error(Errors.INVALID_CHOICE, choice_key)

    return errors

def validate_string_fields(importrow):
    errors = False
    for field in [Fields.ADDRESS, Fields.GENUS, Fields.SPECIES,
                  Fields.CULTIVAR, Fields.SCI_NAME, Fields.URL,
                  Fields.NOTES, Fields.OWNER, Fields.SPONSOR,
                  Fields.STEWARD, Fields.DATA_SOURCE]:
        if field in importrow.datadict:
            value = importrow.datadict[field]

            if len(value) > 255:
                importrow.append_error(Errors.STRING_TOO_LONG, field)
                errors = True
            else:
                importrow.cleaned[field] = value

    return errors

def validate_date_fields(importrow):
    if Fields.DATE_PLANTED in importrow.datadict:
        datestr = importrow.datadict[Fields.DATE_PLANTED]

        if datestr:
            try:
                datep = datetime.strptime(datestr, '%Y-%m-%d')
                importrow.cleaned[Fields.DATE_PLANTED] = datep
            except ValueError, e:
                importrow.append_error(Errors.INVALID_DATE,
                                       Fields.DATE_PLANTED)
                return False

    return True


def validate_and_convert_datatypes(importrow):
    validate_numeric_fields(importrow)
    validate_boolean_fields(importrow)
    validate_choice_fields(importrow)
    validate_string_fields(importrow)
    validate_date_fields(importrow)

def validate_row(importrow):
    """
    Validate a row. Returns True if there were no fatal errors,
    False otherwise

    The method mutates importrow in two ways:
    - The 'errors' field on importrow will be appended to
      whenever an error is found
    - The 'cleaned' field on importrow will be set as fields
      get validated
    """

    # NOTE: Validations append errors directly to importrow
    # and move data over to the 'cleaned' hash as it is
    # validated

    # Convert all fields to correct datatypes
    validate_and_convert_datatypes(importrow)

    # We can work on the 'cleaned' data from here on out
    validate_otm_id(importrow)

    # Attaches a GEOS point to Fields.POINT
    validate_geom(importrow)

    # This could be None or not set if there
    # was an earlier error
    pt = importrow.cleaned.get(Fields.POINT, None)

    validate_species(importrow)

    # This could be None or unset if species data were
    # not given
    species = importrow.cleaned.get(Fields.SPECIES_OBJECT, None)

    # These validations are non-fatal
    if species:
        validate_species_dbh_max(importrow, species)
        validate_species_height_max(importrow, species)

    if pt:
        validate_proximity(importrow, pt)

    importrow.save()

    return not importrow.has_fatal_error()
