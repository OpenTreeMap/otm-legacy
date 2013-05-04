from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from treemap.models import Plot
from importer import fields
from importer import errors

from datetime import datetime

from treemap.models import Species, Neighborhood, Plot,\
    Tree, ExclusionMask

import json

class TreeImportEvent(models.Model):
    """
    A TreeImportEvent represents an attempt to upload a csv containing
    tree/plot information
    """

    # Original Name of the file
    file_name = models.CharField(max_length=255)

    # We can do some numeric conversions
    # TODO: Support numeric conversions
    plot_length_conversion_factor = models.FloatField(default=1.0)
    plot_width_conversion_factor = models.FloatField(default=1.0)
    diameter_conversion_factor = models.FloatField(default=1.0)
    tree_height_conversion_factor = models.FloatField(default=1.0)
    canopy_height_conversion_factor = models.FloatField(default=1.0)

    # Global errors and notices (json)
    errors = models.TextField(default='')

    # Metadata about this particular import
    owner = models.ForeignKey(User)
    created = models.DateTimeField(auto_now=True)
    completed = models.DateTimeField(null=True,blank=True)

    # When false, this dataset is in 'preview' mode
    # When true this dataset has been written to the
    # database
    commited = models.BooleanField(default=False)

    def append_error(self, err, data=None):
        code, msg, fatal = err

        if self.errors is None or self.errors == '':
            self.errors = '[]'

        self.errors = json.dumps(
            self.errors_as_array()+ [
                {'code': code,
                 'msg': msg,
                 'data': data,
                 'fatal': fatal}])

        return self

    def errors_as_array(self):
        if self.errors is None or self.errors == '':
            return []
        else:
            return json.loads(self.errors)

    def has_errors(self):
        return len(self.errors_as_array()) > 0

    def rows(self):
        return self.treeimportrow_set.order_by('idx').all()

    def validate_main_file(self):
        """
        Make sure the imported file has rows and valid columns
        """
        if self.treeimportrow_set.count() == 0:
            self.append_error(errors.EMPTY_FILE)

            # This is a fatal error. We need to have at least
            # one row to get header info
            self.save()
            return False

        has_errors = False
        datastr = self.treeimportrow_set.all()[0].data
        input_fields = set(json.loads(datastr).keys())

        # Point x/y fields are required
        if (fields.POINT_X not in input_fields or
            fields.POINT_Y not in input_fields):
            has_errors = True
            self.append_error(errors.MISSING_POINTS)

        # It is a warning if there are extra input fields
        rem = input_fields - fields.ALL
        if len(rem) > 0:
            has_errors = True
            self.append_error(errors.UNMATCHED_FIELDS, list(rem))

        if errors:
            self.save()

        return not has_errors




class TreeImportRow(models.Model):
    """
    A row of data and import status
    """

    # JSON dictionary from header <-> rows
    data = models.TextField()

    # Row index from original file
    idx = models.IntegerField()

    finished = models.BooleanField(default=False)

    # JSON field containing error information
    errors = models.TextField(default='')

    # plot that was created from this row
    plot = models.ForeignKey(Plot, null=True, blank=True)

    # The main import event
    import_event = models.ForeignKey(TreeImportEvent)

    # Status
    SUCCESS=0
    ERROR=1
    WATCH=2
    WAITING=3
    VERIFIED=4

    status = models.IntegerField(default=WAITING)

    def __init__(self, *args, **kwargs):
        super(TreeImportRow, self).__init__(*args,**kwargs)
        self.jsondata = None
        self.cleaned = {}

    @property
    def datadict(self):
        if self.jsondata is None:
            self.jsondata = json.loads(self.data)

        return self.jsondata

    @datadict.setter
    def datadict(self, v):
        self.jsondata = v
        self.data = json.dumps(self.jsondata)

    def errors_as_array(self):
        if self.errors is None or self.errors == '':
            return []
        else:
            return json.loads(self.errors)

    def has_errors(self):
        return len(self.errors_as_array()) > 0

    def get_fields_with_error(self):
        data = {}
        datadict = self.datadict

        for e in self.errors_as_array():
            for field in e['fields']:
                data[field] = datadict[field]

        return data

    def has_fatal_error(self):
        if self.errors:
            for err in json.loads(self.errors):
                if err['fatal']:
                    return True

        return False


    def append_error(self, err, fields, data=None):
        code, msg, fatal = err

        if self.errors is None or self.errors == '':
            self.errors = '[]'

        # If you give append_error a single field
        # there is no need to get angry
        if isinstance(fields, basestring):
            fields = (fields,) # make into tuple

        self.errors = json.dumps(
            json.loads(self.errors) + [
                {'code': code,
                 'fields': fields,
                 'msg': msg,
                 'data': data,
                 'fatal': fatal}])

        return self


    def validate_species(self):
        genus = self.datadict.get(fields.GENUS,'')
        species = self.datadict.get(fields.SPECIES,'')
        cultivar = self.datadict.get(fields.CULTIVAR,'')

        if genus != '' or species != '' or cultivar != '':
            matching_species = Species.objects\
                                      .filter(genus__iexact=genus)\
                                      .filter(species__iexact=species)\
                                      .filter(cultivar_name__iexact=cultivar)

            if len(matching_species) == 1:
                self.cleaned[fields.SPECIES_OBJECT] = matching_species[0]
            else:
                self.append_error(errors.INVALID_SPECIES,
                                  (fields.GENUS, fields.SPECIES, fields.CULTIVAR),
                                  ' '.join([genus,species,cultivar]).strip())
                return False

        return True

    def safe_float(self, fld):
        try:
            return float(self.datadict[fld])
        except:
            self.append_error(errors.FLOAT_ERROR, fld)
            return False

    def safe_bool(self, fld):
        """ Returns a tuple of (success, bool value) """
        v = self.datadict.get(fld, '').lower()

        if v == 'true':
            return (True,True)
        elif v == 'false':
            return (True,False)
        else:
            self.append_error(errors.BOOL_ERROR, fld)
            return (False,None)


    def safe_int(self, fld):
        try:
            return int(self.datadict[fld])
        except:
            self.append_error(errors.INT_ERROR, fld)
            return False

    def safe_pos_int(self, fld):
        i = self.safe_int(fld)

        if i is False:
            return False
        elif i < 0:
            self.append_error(errors.POS_INT_ERROR, fld)
            return False
        else:
            return i

    def safe_pos_float(self, fld):
        i = self.safe_float(fld)

        if i is False:
            return False
        elif i < 0:
            self.append_error(errors.POS_FLOAT_ERROR, fld)
            return False
        else:
            return i

    def validate_geom(self):
        x = self.cleaned.get(fields.POINT_X, None)
        y = self.cleaned.get(fields.POINT_Y, None)

        # Note, this shouldn't really happen since main
        # file validation will fail, but butter safe than sorry
        if x is None or y is None:
            self.append_error(errors.MISSING_POINTS,
                              (fields.POINT_X, fields.POINT_Y))
            return False

        # Simple validation
        # longitude must be between -180 and 180
        # latitude must be betwen -90 and 90
        if abs(x) > 180 or abs(y) > 90:
            self.append_error(errors.INVALID_GEOM,
                              (fields.POINT_X, fields.POINT_Y))
            return False

        p = Point(x,y)

        if ExclusionMask.objects.filter(geometry__contains=p).exists():
            self.append_error(errors.EXCL_ZONE,
                              (fields.POINT_X, fields.POINT_Y))
            return False
        elif Neighborhood.objects.filter(geometry__contains=p).exists():
            self.cleaned[fields.POINT] = p
        else:
            self.append_error(errors.GEOM_OUT_OF_BOUNDS,
                              (fields.POINT_X, fields.POINT_Y))
            return False

        return True

    def validate_otm_id(self):
        oid = self.cleaned.get(fields.OPENTREEMAP_ID_NUMBER, None)
        if oid:
            has_plot = Plot.objects.filter(
                pk=oid).exists()

            if not has_plot:
                self.append_error(errors.INVALID_OTM_ID,
                                  fields.OPENTREEMAP_ID_NUMBER)
                return False

        return True

    def validate_proximity(self, point):
        nearby = Plot.objects\
                     .filter(present=True,
                             geometry__distance_lte=(point, D(ft=10.0)))\
                     .distance(point)\
                     .order_by('distance')[:5]

        if len(nearby) > 0:
            self.append_error(errors.NEARBY_TREES,
                              (fields.POINT_X, fields.POINT_Y),
                              [p.pk for p in nearby])
            return False
        else:
            return True

    def validate_species_max(self, field, max_val, err):
        inputval = self.cleaned.get(field, None)
        if inputval:
            if max_val and inputval > max_val:
                self.append_error(err, field, max_val)
                return False

        return True


    def validate_species_dbh_max(self, species):
        return self.validate_species_max(
            fields.DIAMETER,
            species.v_max_dbh, errors.SPECIES_DBH_TOO_HIGH)

    def validate_species_height_max(self, species):
        return self.validate_species_max(
            fields.TREE_HEIGHT,
            species.v_max_height, errors.SPECIES_HEIGHT_TOO_HIGH)

    def validate_numeric_fields(self):
        def cleanup(fields, fn):
            has_errors = False
            for f in fields:
                if f in self.datadict and self.datadict[f]:
                    maybe_num = fn(f)

                    if maybe_num is False:
                        has_errors = True
                    else:
                        self.cleaned[f] = maybe_num

            return has_errors

        pfloat_ok = cleanup([fields.PLOT_WIDTH, fields.PLOT_LENGTH,
                             fields.DIAMETER, fields.TREE_HEIGHT,
                             fields.CANOPY_HEIGHT], self.safe_pos_float)

        float_ok = cleanup([fields.POINT_X, fields.POINT_Y],
                           self.safe_float)

        int_ok = cleanup([fields.OPENTREEMAP_ID_NUMBER,
                          fields.ORIG_ID_NUMBER],
                         self.safe_pos_int)

        return pfloat_ok and float_ok and int_ok

    def validate_boolean_fields(self):
        has_errors = False
        for f in [fields.READ_ONLY, fields.TREE_PRESENT]:
            if f in self.datadict:
                success, v = self.safe_bool(f)
                if success:
                    self.cleaned[f] = v
                else:
                    has_errors = True

        return has_errors

    def validate_choice_fields(self):
        has_errors = False
        for field,choice_key in fields.CHOICE_MAP.iteritems():
            value = self.datadict.get(field, None)
            if value:
                all_choices = settings.CHOICES[choice_key]
                choices = { value for (id,value) in all_choices }

                if value in choices:
                    # Some plot choice fields aren't automatically
                    # converting to choice values so we do it forcibly
                    # here
                    if field in fields.PLOT_CHOICES:
                        self.cleaned[field] = [id for (id,v)
                                                    in all_choices
                                                    if v == value][0]
                    else:
                        self.cleaned[field] = value
                else:
                    has_errors = True
                    self.append_error(errors.INVALID_CHOICE,
                                      field, choice_key)

        return has_errors

    def validate_string_fields(self):
        has_errors = False
        for field in [fields.ADDRESS, fields.GENUS, fields.SPECIES,
                      fields.CULTIVAR, fields.SCI_NAME, fields.URL,
                      fields.NOTES, fields.OWNER, fields.SPONSOR,
                      fields.STEWARD, fields.DATA_SOURCE,
                      fields.LOCAL_PROJECTS, fields.NOTES]:

            if field in self.datadict:
                value = self.datadict[field]

                if len(value) > 255:
                    self.append_error(errors.STRING_TOO_LONG, field)
                    has_errors = True
                else:
                    self.cleaned[field] = value

        return has_errors

    def validate_date_fields(self):
        if fields.DATE_PLANTED in self.datadict:
            datestr = self.datadict[fields.DATE_PLANTED]

            if datestr:
                try:
                    datep = datetime.strptime(datestr, '%Y-%m-%d')
                    self.cleaned[fields.DATE_PLANTED] = datep
                except ValueError, e:
                    self.append_error(errors.INVALID_DATE,
                                      fields.DATE_PLANTED)
                    return False

        return True


    def validate_and_convert_datatypes(self):
        self.validate_numeric_fields()
        self.validate_boolean_fields()
        self.validate_choice_fields()
        self.validate_string_fields()
        self.validate_date_fields()

    def validate_row(self):
        """
        Validate a row. Returns True if there were no fatal errors,
        False otherwise

        The method mutates self in two ways:
        - The 'errors' field on self will be appended to
          whenever an error is found
        - The 'cleaned' field on self will be set as fields
          get validated
        """
        # Clear errrors
        self.errors = ''

        # NOTE: Validations append errors directly to importrow
        # and move data over to the 'cleaned' hash as it is
        # validated

        # Convert all fields to correct datatypes
        self.validate_and_convert_datatypes()

        # We can work on the 'cleaned' data from here on out
        self.validate_otm_id()

        # Attaches a GEOS point to fields.POINT
        self.validate_geom()

        # This could be None or not set if there
        # was an earlier error
        pt = self.cleaned.get(fields.POINT, None)

        self.validate_species()

        # This could be None or unset if species data were
        # not given
        species = self.cleaned.get(fields.SPECIES_OBJECT, None)

        # These validations are non-fatal
        if species:
            self.validate_species_dbh_max(species)
            self.validate_species_height_max(species)

        if pt:
            self.validate_proximity(pt)

        fatal = False
        if self.has_fatal_error():
            self.status = TreeImportRow.ERROR
            fatal = True
        elif self.has_errors(): # Has 'warning'/tree watch errors
            self.status = TreeImportRow.WATCH
        else:
            self.status = TreeImportRow.VERIFIED

        self.save()
        return not fatal

    def commit_row(self):
        # First validate
        if not self.validate_row():
            return False

        #TODO: This is a kludge to get it to work with the
        #      old system. Once everything works we can drop
        #      this code
        from treemap.models import ImportEvent

        objs = ImportEvent.objects.filter(file_name=self.import_event.file_name)
        if len(objs) == 0:
            import_event = ImportEvent(file_name=self)
            import_event.save()
        else:
            import_event = objs[0]
        #
        # END OF KLUDGE
        #

        # Get our data
        data = self.cleaned

        plot_edited = False
        tree_edited = False

        # Initially grab plot from row if it exists
        plot = self.plot
        if plot is None:
            plot = Plot(present=True)

        # Event if TREE_PRESENT is None, a tree
        # can still be spawned here if there is
        # any tree data later
        tree = plot.current_tree()

        # Check for an existing tree:
        if fields.OPENTREEMAP_ID_NUMBER in data:
            plot = Plot.objects.get(
                pk=data[fields.OPENTREEMAP_ID_NUMBER])
            tree = plot.current_tree()
        else:
            if data.get(fields.TREE_PRESENT, False):
                tree_edited = True
                if tree is None:
                    tree = Tree(present=True)

        data_owner = self.import_event.owner

        plot_map = {
            'geometry': fields.POINT,
            'width': fields.PLOT_WIDTH,
            'length': fields.PLOT_LENGTH,
            'type': fields.PLOT_TYPE,
            'readonly': fields.READ_ONLY,
            'sidewalk_damage': fields.SIDEWALK,
            'powerline_conflict_potential': fields.POWERLINE_CONFLICT,
            'owner_orig_id': fields.ORIG_ID_NUMBER,
            'owner_additional_id': fields.DATA_SOURCE,
            'owner_additional_properties': fields.NOTES
        }

        tree_map = {
            'tree_owner': fields.OWNER,
            'steward_name': fields.STEWARD,
            'dbh': fields.DIAMETER,
            'height': fields.TREE_HEIGHT,
            'canopy_height': fields.CANOPY_HEIGHT,
            'species': fields.SPECIES_OBJECT,
            'sponsor': fields.SPONSOR,
            'date_planted': fields.DATE_PLANTED,
            'readonly': fields.READ_ONLY,
            'projects': fields.LOCAL_PROJECTS,
            'condition': fields.TREE_CONDITION,
            'canopy_condition': fields.CANOPY_CONDITION,
            'url': fields.URL,
            'pests': fields.PESTS
        }

        for modelkey, importdatakey in plot_map.iteritems():
            importdata = data.get(importdatakey, None)

            if importdata:
                plot_edited = True
                setattr(plot, modelkey, importdata)

        if plot_edited:
            plot.last_updated_by = data_owner
            plot.import_event = import_event
            plot.save()

        for modelkey, importdatakey in tree_map.iteritems():
            importdata = data.get(importdatakey, None)

            if importdata:
                tree_edited = True
                if tree is None:
                    tree = Tree(present=True)
                setattr(tree, modelkey, importdata)

        if tree_edited:
            tree.last_updated_by = data_owner
            tree.import_event = import_event
            tree.plot = plot
            tree.save()

        self.plot = plot
        self.status = TreeImportRow.SUCCESS
        self.save()

        return True

    #TODO: Ok to ignore address?
    #TODO: Tree actions (csv field?)
