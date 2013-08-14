import os
import math
import re
from decimal import *
from datetime import datetime
from itertools import chain
from operator import itemgetter
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Sum, Q
from django.contrib.gis.measure import D
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction

import audit
from classfaves.models import FavoriteBase
import logging
import simplejson
from sorl.thumbnail import ImageField
from threadedcomments.models import ThreadedComment

from treemap.eco_benefits import set_environmental_summaries

status_choices = (
        ('height','Height (in feet)'),
        ('dbh','Diameter (in inches)'),
        ('condition','Condition'),
        ('sidewalk_damage','Sidewalk Damage'),
        ('canopy_height', 'Canopy Height (in feet)'),
        ('canopy_condition', 'Canopy Condition')
    )

choices_choices = (
    ('factoid', 'Factoid'),
    ('plot', 'Plot'),
    ('alert', 'Alert'),
    ('action', 'Action'),
    ('local', 'Local'),
    ('sidewalk_damage', 'Sidewalk Damage'),
    ('condition', 'Condition'),
    ('canopy_condition', 'Canopy Condition')
)
watch_choices = {
    "height_dbh": "Height to DBH Ratio",
    "proximity": "Trees Nearby",
    "canopy_condition": "Canopy-Condition Matching",
    "max_height": "Species Height",
    "max_dbh": "Species DBH",
}
watch_tests = {
    "height_dbh": 'validate_height_dbh',
    "proximity": 'validate_proximity',
    "canopy_condition": 'validate_canopy_condition',
    "max_height": 'validate_max_dbh',
    "max_dbh": 'validate_max_height',
}

data_types = (
    ('text', 'text'),
    ('int', 'int'),
    ('float', 'float'),
    ('bool', 'bool'),
    ('geo', 'geo'),
)

class BenefitValues(models.Model):
    area = models.CharField(max_length=255)
    stormwater = models.FloatField()
    electricity = models.FloatField()
    natural_gas = models.FloatField()
    co2 = models.FloatField()
    ozone = models.FloatField()
    nox = models.FloatField()
    pm10 = models.FloatField()
    sox = models.FloatField()
    voc = models.FloatField()
    bvoc = models.FloatField()

    def __unicode__(self): return u'%s' % (self.area)


class CommentFlag(models.Model):
    flagged = models.BooleanField(default=False)
    flagged_date = models.DateTimeField(auto_now=True)

    comment = models.ForeignKey(ThreadedComment, related_name="comment_flags")
    user = models.ForeignKey(User)

def sorted_nicely(l, key):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda item: [ convert(c) for c in re.split('([0-9]+)', key(item)) ]
    return sorted(l, key = alphanum_key)


# GEOGRAPHIES #
class Neighborhood(models.Model):
    """
    Restricts point placement to within these boundaries.
    """
    name = models.CharField(max_length=255)
    region_id = models.IntegerField()
    city = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()

    def __unicode__(self): return u'%s' % self.name


class SupervisorDistrict(models.Model):
    """
    not used currently
    """
    id = models.IntegerField(primary_key=True)
    supervisor = models.CharField(max_length=255)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()

    def __unicode__(self): return u'%s (%s)' % (self.id, self.supervisor)


class ZipCode(models.Model):
    """
    Display and searching only
    """
    zip = models.CharField(max_length=255)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()

    def __unicode__(self): return u'%s' % (self.zip)


class ExclusionMask(models.Model):
    """
    Further restrict point placement if settings.MASKING_ON = True
    """
    geometry = models.MultiPolygonField(srid=4326)
    type = models.CharField(max_length=50, blank=True, null=True)
    objects=models.GeoManager()


class Resource(models.Model):
    """
    For use in STRATUM - a Resource can have many species,
    and has different values for each dbh/resource combo.
    """
    meta_species = models.CharField(max_length=150, null=True, blank=True)
    region = models.CharField(max_length=150, null=True, blank=True)

    def __unicode__(self): return u'%s' % (self.meta_species)


class ClimateZone(models.Model):
    itree_region = models.CharField(max_length=40)
    geometry = models.MultiPolygonField(srid=4326)

    objects = models.GeoManager()

class Species(models.Model):
    """
        http://plants.usda.gov/java/AdvancedSearchServlet?pfa=na&statefips=us
        &statefips=usterr&statefips=CAN&grwhabt=Tree&dsp_symbol=on
        &dsp_vernacular=on&dsp_pfa=on&dsp_statefips=on&dsp_grwhabt=on
        &dsp_nativestatuscode=on&dsp_fed_nox_status_ind=on&dsp_state_nox_status=on
        &dsp_invasive_pubs=on&dsp_fed_te_status=on&dsp_state_te_status=on
        &dsp_nat_wet_ind=on&dsp_wet_region=on&dsp_fall_cspc_ind=on
        &dsp_fire_resist_ind=on&dsp_flwr_cspc_ind=on&dsp_bloom_prd_cd=on
        &dsp_frut_seed_abund_cd=on&dsp_frut_seed_start_cd=on&dsp_frut_seed_end_cd=on
        &dsp_frut_body_suit_ind=on&dsp_palat_human_ind=on&Synonyms=all&viewby=sciname
    """
    symbol = models.CharField(max_length=255)
    alternate_symbol = models.CharField(max_length=255, null=True, blank=True)
    itree_code = models.CharField(max_length=255, null=True, blank=True)
    scientific_name = models.CharField(max_length=255)
    genus = models.CharField(max_length=255)
    species = models.CharField(max_length=255, null=True, blank=True) #sometimes we just have genus/cultivar combo
    cultivar_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    common_name = models.CharField(max_length=255, null=True, blank=True)
    family = models.CharField(max_length=255,null=True,blank=True)
    other_part_of_name = models.CharField(max_length=255,null=True,
                                          blank=True,default='')

    native_status = models.CharField(max_length=255, null=True, blank=True)
    bloom_period = models.CharField(max_length=255, null=True, blank=True)
    fruit_period = models.CharField(max_length=255, null=True, blank=True)
    fall_conspicuous = models.NullBooleanField()
    flower_conspicuous = models.NullBooleanField()
    palatable_human = models.NullBooleanField()
    wildlife_value = models.NullBooleanField()

    fact_sheet = models.URLField(max_length=255, null=True, blank=True)
    plant_guide = models.URLField(max_length=255, null=True, blank=True)

    tree_count = models.IntegerField(default=0, db_index=True)

    v_max_dbh = models.IntegerField(null=True, blank=True)
    v_max_height = models.IntegerField(null=True, blank=True)
    v_multiple_trunks = models.NullBooleanField()

    resource = models.ManyToManyField(Resource, null=True)
    objects = models.GeoManager()

    #tree_count should always be set on tree update..
    def save(self,*args,**kwargs):
        self.tree_count = self.tree_set.filter(present=True).count()
        name = '%s' % self.genus
        if self.species and self.species != '':
            name += " %s" % self.species
        #if self.cultivar_name and self.cultivar_name != '':
        #    name += " %s" % self.cultivar_name
        self.scientific_name = name
        super(Species, self).save(*args,**kwargs)

    def __unicode__(self):
        if self.cultivar_name:
            return u"%s, '%s'" % (self.common_name,self.cultivar_name)
        else:
            return u'%s' % (self.common_name)


class GeocodeCache(models.Model):
    address_street = models.CharField(max_length=256)
    geocoded_address = models.CharField(max_length=256)
    geocoded_lat = models.FloatField(null=True)
    geocoded_lon  = models.FloatField(null=True)
    geocoded_accuracy = models.IntegerField(null=True)
    geocoded_geometry = models.PointField(null=True, srid=4326)
    geometry = models.PointField(null=True, srid=4326)
    objects = models.GeoManager()

class ImportEvent(models.Model):
    file_name = models.CharField(max_length=256)
    import_date = models.DateField(auto_now=True)

class PlotLocateManager(models.GeoManager):

    def with_geometry(self, geom, distance=0, max_plots=1, species_preferenece=None,
                      native=None, flowering=None, fall=None, edible=None, pests=None,
                      dbhmin=None, dbhmax=None, species=None, sort_recent=None,
                      sort_pending=None, has_tree=None, has_species=None, has_dbh=None):
        '''
        Return a QuerySet with trees near a Point geometry or intersecting a Polygon geometry
        '''
        plots = Plot.objects.filter(present=True)

        if geom.geom_type == 'Point':
            plots = plots.filter(geometry__dwithin=(geom, float(distance))).distance(geom).order_by('distance')
        else:
            plots = plots.filter(geometry__intersects=geom)

        if species_preferenece:
            plots_filtered_by_species_preference = plots.filter(tree__species__id=species_preferenece, tree__present=True)
            # If a species_preferenece is specified then any nearby trees with that species_preferenece will be
            # returned. If there are no trees for that species_preferenece, the nearest tree from any
            # species_preferenece will be returned.
            if len(plots_filtered_by_species_preference) > 0:
                plots = plots_filtered_by_species_preference

        if species: # Note that, unlike "preference", these values are forced
            plots = plots.filter(tree__species__pk=species, tree__present=True)

        if native is not None:
            if native:
                native = "True"
            else:
                native = ""

            plots = plots.filter(tree__species__native_status=native, tree__present=True)

        if flowering is not None:
            plots = plots.filter(tree__species__flower_conspicuous=flowering, tree__present=True)

        if fall is not None:
            plots = plots.filter(tree__species__fall_conspicuous=fall, tree__present=True)

        if edible is not None:
            plots = plots.filter(tree__species__palatable_human=edible, tree__present=True)

        if dbhmin is not None:
            plots = plots.filter(tree__dbh__gte=dbhmin, tree__present=True)

        if dbhmax is not None:
            plots = plots.filter(tree__dbh__lte=dbhmax, tree__present=True)

        if pests is not None:
            plots = plots.filter(tree__pests=pests)

        has_filter_q = None
        def filter_or(f,has):
            if has:
                return f | has
            else:
                return f

        if has_tree is not None:
            q_has_tree = Q(tree__present=True)
            if not has_tree:
                q_has_tree = ~q_has_tree

            has_filter_q = filter_or(q_has_tree, has_filter_q)

        if has_species is not None:
            if has_species:
                q_has_species = Q(tree__species__isnull=False,tree__present=True)
            else:
                # Note that Q(tree__present=False) seems to exlucde too
                # many records. Instead ~Q(tree__present=True) selects
                # all plots without tree records and those with trees
                # that are marked as not present
                q_has_species = Q(tree__species__isnull=True,tree__present=True)|(~Q(tree__present=True))

            has_filter_q = filter_or(q_has_species, has_filter_q)

        if has_dbh is not None:
            q_has_dbh = Q(tree__dbh__isnull=(not has_dbh))
            has_filter_q = filter_or(q_has_dbh, has_filter_q)

        if has_filter_q:
            plots = plots.filter(has_filter_q)

        if sort_recent:
            plots = plots.order_by('-last_updated')

        if sort_pending:
            plots_tree_pending = plots.filter(Q(tree__treepending__status='pending'))
            plots_plot_pending = plots.filter(Q(plotpending__status='pending'))

            if max_plots:
                plots = list(plots_tree_pending) + list(plots_plot_pending)
                # Uniquify
                plots_hash = {}
                for p in plots:
                    plots_hash[p.pk] = p

                plots = plots_hash.values()

                plots = sorted(plots, key=lambda z: z.distance)

                plots = plots[:max_plots]

                extent = self.calc_extent(plots)

        else:
            if max_plots:
                plots = plots[:max_plots]

            if plots.count() > 0:
                extent = plots.extent()
            else:
                extent = []

        return plots, extent

    def calc_extent(self, plots):
        if not plots:
            return []

        xs = [plot.geometry.x for plot in plots]
        ys = [plot.geometry.y for plot in plots]

        return (min(xs),min(ys),max(xs),max(ys))

class ManagementMixin(object):
    """
    Methods that relate to checking editabilty, usable in either Tree or Plot models
    """
    def _created_by(self):
        insert_event_set = self.history.filter(_audit_change_type='I')
        if insert_event_set.count() == 0:
            # If there is no audit event with type 'I' then the user who created the model cannot be determined
            return None
        else:
            # The 'auth.change_user' permission is a proxy for 'is the user a manager'
            return insert_event_set[0].last_updated_by
    created_by = property(_created_by)

    def _was_created_by_a_manager(self):
        if self.created_by:
            return self.created_by.has_perm('auth.change_user')
        else:
            # If created_by is None, the author of the instance could not be
            # determined (bulk loaded data, perhaps). In this case we assume, for
            # for safety, that the instance was created by a manager
            return True
    was_created_by_a_manager = property(_was_created_by_a_manager)

class PendingMixin(object):
    """
    Methods that relate to pending edit management for either Tree or Plot models
    """
    def get_active_pends(self):
        raise Exception('PendingMixin expects subclasses to implement get_active_pends')

    def get_active_pend_dictionary(self):
        """
        Create a dictionary of active pends keyed by field name.

        {
          'field1': {
            'latest_value': 4,
            'pends': [
              <Pending>,
              <Pending>
            ]
          },
          'field2': {
            'latest_value': 'oak',
            'pends': [
              <Pending>
            ]
          }
        }
        """
        pends = self.get_active_pends().order_by('-submitted')

        result = {}
        for pend in pends:
            if pend.field in result:
                result[pend.field]['pending_edits'].append(pend)
            else:
                result[pend.field] = {'latest_value': pend.value, 'pending_edits': [pend]}
        return result


class Plot(models.Model, ManagementMixin, PendingMixin):
    present = models.BooleanField(default=True)
    width = models.FloatField(null=True, blank=True, error_messages={'invalid': "Error: This value must be a number."})
    length = models.FloatField(null=True, blank=True, error_messages={'invalid': "Error: This value must be a number."})

    type = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["plot_types"])
    powerline_conflict_potential = models.CharField(max_length=256, choices=settings.CHOICES["powerlines"],
        help_text = "Are there overhead powerlines present?",null=True, blank=True)
    sidewalk_damage = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["sidewalks"])

    address_street = models.CharField(max_length=256, blank=True, null=True)
    address_city = models.CharField(max_length=256, blank=True, null=True)
    address_zip = models.CharField(max_length=30,blank=True, null=True)
    neighborhood = models.ManyToManyField(Neighborhood, null=True)
    neighborhoods = models.CharField(max_length=150, null=True, blank=True) # Really this should be 'blank=True' and null=False
    zipcode = models.ForeignKey(ZipCode, null=True, blank=True) # Because it is calculated in the save method

    geocoded_accuracy = models.IntegerField(null=True, blank=True)
    geocoded_address = models.CharField(max_length=256, null=True, blank=True)
    geocoded_lat = models.FloatField(null=True, blank=True)
    geocoded_lon  = models.FloatField(null=True, blank=True)

    geometry = models.PointField(srid=4326)

    #geocoded_geometry = models.PointField(null=True, srid=4326)
    #owner_geometry = models.PointField(null=True, srid=4326) #should we keep this?

    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='plot_updated_by') # TODO set to current user

    history = audit.AuditTrail()
    import_event = models.ForeignKey(ImportEvent)
    objects = models.GeoManager()
    # The locate Manager encapsulates plot search functionality
    locate = PlotLocateManager()

    #original data to help owners associate back to their own db
    data_owner = models.ForeignKey(User, related_name="owner", null=True, blank=True)
    owner_orig_id = models.CharField(max_length=256, null=True, blank=True)
    owner_additional_id = models.CharField(max_length=255, null=True, blank=True)
    owner_additional_properties = models.TextField(null=True, blank=True, help_text = "Additional Properties (not searchable)")

    readonly = models.BooleanField(default=False)

    def itree_region(self):
        zone = ClimateZone.objects.filter(geometry__contains=self.geometry)

        if len(zone) == 0:
            return None
        else:
            return zone[0].itree_region

    def validate(self):
        self.full_clean()
        em = ExclusionMask.objects.filter(geometry__contains=self.geometry)
        if em.count() > 0:
            raise ValidationError("Geometry may not be within an exclusion zone.")


    def get_plot_type_display(self):
        for key, value in settings.CHOICES["plot_types"]:
            if key == self.type:
                return value
        return None

    def get_plot_size(self):
        length = self.length
        width = self.width
        if length == None: length = 'Missing'
        elif length == 99: length = '15+ ft'
        else: length = '%.2f ft' % length
        if width == None: width = 'Missing'
        elif width == 99: width = '15+ ft'
        else: width = '%.2f ft' % width
        #print length, width
        return '%s x %s' % (length, width)

    def get_sidewalk_damage_display(self):
        for key, value in settings.CHOICES["sidewalks"]:
            if key == self.sidewalk_damage:
                return value
        return None

    def get_powerline_conflict_display(self):
        for key, value in settings.CHOICES["powerlines"]:
            if key == self.powerline_conflict_potential:
                return value
        return None


    def get_stewardship_count(self):
        return len(self.plotstewardship_set.all())

    def current_tree(self):
        trees = self.tree_set.filter(present=True)
        if trees.count() > 0:
            return trees[0]
        else:
            return None

    def get_active_pends(self):
        pends = self.plotpending_set.filter(status='pending')
        return pends

    def get_active_geopends(self):
        pends = self.plotpending_set.filter(status='pending').exclude(geometry=None)
        return pends

    def get_active_pends_with_tree_pends(self):
        plot_pends = self.plotpending_set.filter(status='pending')
        if self.current_tree():
            tree_pends = self.current_tree().get_active_pends()
        else:
            tree_pends = []
        pends = list(chain(plot_pends, tree_pends))
        return pends

    def get_plot_size(self):
        length = self.length
        width = self.width
        if length == None: length = 'Missing'
        elif length == 99: length = '15+ ft'
        else: length = '%.2f ft' % length
        if width == None: width = 'Missing'
        elif width == 99: width = '15+ ft'
        else: width = '%.2f ft' % width
        return '%s x %s' % (length, width)

    def quick_save(self, *args, **kwargs):
        super(Plot, self).save(*args,**kwargs)

    def save(self, *args, **kwargs):
        self.validate()

        pnt = self.geometry

        n = Neighborhood.objects.filter(geometry__contains=pnt)
        z = ZipCode.objects.filter(geometry__contains=pnt)

        if n:
            oldns = self.neighborhoods
            new_nhoods = []
            for nhood in n:
                if nhood:
                    new_nhoods.append(nhood.id.__str__())
            self.neighborhoods = " ".join(new_nhoods)
        else:
            self.neighborhoods = ""
            oldns = None

        if self.id:
            oldn = self.neighborhood.all()
            oldz = self.zipcode
        else:
            oldn = []
            oldz = None

        super(Plot, self).save(*args,**kwargs)
        if n:
            self.neighborhood.clear()
            for nhood in n:
                if nhood:
                    self.neighborhood.add(nhood)
        else:
            self.neighborhood.clear()
        if z: self.zipcode = z[0]
        else: self.zipcode = None

        if self.current_tree():
            set_environmental_summaries(self.current_tree())

        super(Plot, self).save(*args,**kwargs)

        if self.neighborhoods != oldns:
            done = []
            if n:
                for nhood in n:
                    if nhood.id in done: continue
                    if self.current_tree():
                        self.current_tree().update_aggregate(AggregateNeighborhood, nhood)
                    else:
                        self.update_aggregate(AggregateNeighborhood, nhood)
                    done.append(nhood.id)
            if oldn:
                for nhood in oldn:
                    if nhood.id in done: continue
                    if self.current_tree():
                        self.current_tree().update_aggregate(AggregateNeighborhood, nhood)
                    else:
                        self.update_aggregate(AggregateNeighborhood, nhood)
                    done.append(nhood.id)

        if self.current_tree() and z and z[0] != oldz:
            if z: self.current_tree().update_aggregate(AggregateZipCode, z[0])
            if oldz: self.current_tree().update_aggregate(AggregateZipCode, oldz)

    def update_aggregate(self, ag_model, location):
        agg =  ag_model.objects.filter(location=location)
        if agg:
            agg = agg[0]
        else:
            agg = ag_model(location=location)
        #print agg.__dict__
        #summaries = []
        trees = Tree.objects.filter(plot__geometry__within=location.geometry)
        plots = Plot.objects.filter(geometry__within=location.geometry)
        #print trees
        agg.total_trees = trees.count()
        agg.total_plots = plots.count()

        agg.save()

    def validate_proximity(self, return_trees=False, max_count=1):
        if not self.geometry:
            return None
        nearby = Plot.objects.filter(present=True, geometry__distance_lte=(self.geometry, D(ft=10.0)))
        if nearby.count() > max_count:
            if return_trees:
                return nearby
            return (nearby.count()-max_count).__str__() #number greater than max_count allows
        return None

    def remove(self):
        """
        Mark the plot and its associated objects as not present.
        """
        if self.current_tree():
            tree = self.current_tree()
            tree.remove()

        self.present = False
        self.save()

        for audit_trail_record in self.history.all():
            audit_trail_record.present = False
            audit_trail_record.save()

class Tree(models.Model, ManagementMixin, PendingMixin):
    def __init__(self, *args, **kwargs):
        super(Tree, self).__init__(*args, **kwargs)  #save, in order to get ID for the tree
    #owner properties based on wiki/DatabaseQuestions
    plot = models.ForeignKey(Plot)
    tree_owner = models.CharField(max_length=256, null=True, blank=True)
    steward_name = models.CharField(max_length=256, null=True, blank=True) #only modifyable by admin
    steward_user = models.ForeignKey(User, null=True, blank=True, related_name="steward") #only modifyable by admin
    sponsor = models.CharField(max_length=256, null=True, blank=True) #only modifyable by us

    species = models.ForeignKey(Species,verbose_name="Scientific name",null=True, blank=True)
    species_other1 = models.CharField(max_length=255, null=True, blank=True)
    species_other2 = models.CharField(max_length=255, null=True, blank=True)
    orig_species = models.CharField(max_length=256, null=True, blank=True)
    dbh = models.FloatField(null=True, blank=True) #gets auto-set on save
    height = models.FloatField(null=True, blank=True, error_messages={'invalid': "Error: This value must be a number."})
    canopy_height = models.FloatField(null=True, blank=True, error_messages={'invalid': "Error: This value must be a number."})
    date_planted = models.DateField(null=True, blank=True)
    date_removed = models.DateField(null=True, blank=True)
    present = models.BooleanField(default=True)

    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='updated_by') # TODO set to current user

    s_order = models.IntegerField(null=True, blank=True)
    photo_count = models.IntegerField(null=True, blank=True)

    objects = models.GeoManager()
    history = audit.AuditTrail()
    projects = models.CharField(max_length=20, null=True, blank=True)

    import_event = models.ForeignKey(ImportEvent)

    condition = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["conditions"])
    canopy_condition = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["canopy_conditions"])

    readonly = models.BooleanField(default=False)
    url = models.URLField(max_length=255, null=True, blank=True)
    pests = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["pests"])

    def has_common_attributes(self):
        if self.get_flag_count > 0:
            return True
        if self.species:
            spp = self.species
            if spp.flower_conspicuous or spp.fall_conspicuous or spp.palatable_human or spp.native_status:
                return True
        return False

    def get_absolute_url(self):
        return "/trees/%i/" % self.id


    def get_display(self, choices, val):
        for key, value in settings.CHOICES[choices]:
            if key == val:
                return value
        return None

    def get_condition_display(self):
        return self.get_display("conditions", self.condition)

    def get_canopy_condition_display(self):
        return self.get_display("canopy_condition", self.canopy_condition)

    def get_pests_display(self):
        return self.get_display("pests",self.pests)

    def get_scientific_name(self):
        if self.species:
            sn = self.species.scientific_name
            if not sn:
                sn = self.species.genus
            if self.species.cultivar_name:
                sn += " '%s'" % self.species.cultivar_name
            return sn
        else:
            return 'unavailable'

    def get_common_name(self):
        if self.species:
            return self.species.common_name
        return 'unavailable'

    def get_eco_impact(self):
        tr =  TreeResource.objects.filter(tree=self)
        if tr:
            return "%0.2f" % tr[0].total_benefit()

    def get_action_count(self):
        return len(self.treeaction_set.all())

    def get_alert_count(self):
        return len(self.treealert_set.all())

    def get_flag_count(self):
        return len(self.treeflags_set.all())

    def get_stewardship_count(self):
        return len(self.treestewardship_set.all())

    def get_active_pends(self):
        pends = self.treepending_set.filter(status='pending')
        return pends

    def is_complete(self):
        if self.species >= 0 and self.dbh:
            return True
        else:
            return False

    def set_species(self, species_id, commit=True):
        """
        sets the species, and updates the species tree count
        """
        self.old_species = self.species
        new_species = Species.objects.get(id=species_id)
        self.species = new_species
        if commit:
            self.save()

    def save(self,*args,**kwargs):
        #save new neighborhood/zip connections if needed
        self.photo_count = self.treephoto_set.count()

        self.projects = ""
        for fl in self.treeflags_set.all():
            self.projects = self.projects + " " + fl.key


        super(Tree, self).save(*args,**kwargs)

        self.quick_save(*args, **kwargs)

    def quick_save(self,*args,**kwargs):
        super(Tree, self).save(*args,**kwargs)
        set_environmental_summaries(self)
        #set new species counts
        if hasattr(self,'old_species') and self.old_species:
            self.old_species.save()
        if hasattr(self,'species') and self.species:
            self.species.save()

        self.plot.last_updated = self.last_updated
        self.plot.save()

    def update_aggregate(self, ag_model, location):
        agg =  ag_model.objects.filter(location=location)
        if agg:
            agg = agg[0]
        else:
            agg = ag_model(location=location)
        #print agg.__dict__
        #summaries = []
        trees = Tree.objects.filter(plot__geometry__within=location.geometry)
        plots = Plot.objects.filter(geometry__within=location.geometry)
        #print trees
        agg.total_trees = trees.count()
        agg.total_plots = plots.count()

        trees = trees.exclude( Q(dbh=None) | Q(dbh=0.0) ).exclude(species=None)
        #print agg.total_trees
        #TODO figure out how to summarize diff stratum stuff
        field_names = [x.name for x in ResourceSummaryModel._meta.fields
            if not x.name == 'id']

        if agg.total_trees == 0:
            for f in field_names:
                setattr(agg, f, 0.0)
        else:
        #TODO speed this up
            for f in field_names:
                fn = 'treeresource__' + f
                s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                setattr(agg,f,s)
        agg.save()


    def percent_complete(self):
        has = 0
        attr = settings.COMPLETE_ARRAY
        for item in attr:
            if hasattr(self,item):
                if getattr(self,item):
                    has +=1
            elif hasattr(self.plot, item):
                if getattr(self.plot, item):
                    has +=1
        return has/float(len(attr))*100

    def validate_all(self):
        #print watch_tests
        for test, method in watch_tests.iteritems():
            #print test
            result = getattr(self, method)()
            #print result

            # check for results and save - passed tests return None
            if not result:
                TreeWatch.objects.filter(tree=self, key=watch_choices[test]).delete()
                continue
            # if identical watch already exists skip it
            if TreeWatch.objects.filter(tree=self, key=watch_choices[test], value=result):
                continue

            TreeWatch.objects.filter(tree=self, key=watch_choices[test]).delete()
            self.treewatch_set.create(
                key=watch_choices[test],
                value=result,
            )

    def validate_proximity(self, return_trees=False, max_count=1):
        if not self.plot.geometry:
            return None
        return self.plot.validate_proximity()


    # Disallowed combinations:
    #   Dead + 0% loss, Dead + 25% loss, Dead + 50% loss, Dead + 75% loss
    #   Excellent + 100% loss, Excellent + 75% loss
    def validate_canopy_condition(self):
        if not self.canopy_condition or not self.condition:
            return None

        cond = self.condition
        c_cond = self.canopy_condition
        if cond == 'Dead':
            if not c_cond == 'Little or None (up to 100% missing)' and not c_cond == 'None' :
                return cond + ", " + c_cond

        elif cond == 'Excellent':
            if c_cond == 'Little or None (up to 100% missing)' or c_cond == 'Large Gaps (up to 75% missing)':
                return cond + ", " + c_cond

        return None

    # discussions: http://www.nativetreesociety.org/measure/tdi/diameter_height_ratio.htm
    def validate_height_dbh(self):
        if not self.height or not self.dbh:
            return None
        getcontext().prec = 3
        cbh = self.dbh * math.pi
        cbh_feet = cbh * .75 / 9
        float_ratio = self.height / cbh_feet
        hd_ratio = Decimal(float_ratio.__str__())
        #print hd_ratio
        if hd_ratio < 100:
            return None
        return round(hd_ratio, 2).__str__()

    def validate_max_dbh(self):
        if not self.dbh or not self.species or not self.species.v_max_dbh:
            return None
        if self.dbh > self.species.v_max_dbh:
            return "%s (species max: %s )" % (str(self.dbh), str(self.species.v_max_dbh))
        return None

    def validate_max_height(self):
        if not self.height or not self.species or not self.species.v_max_height:
            return None
        if self.height > self.species.v_max_height:
            return "%s (species max: %s)" % (str(self.height), str(self.species.v_max_height))
        return None

    def remove(self):
        """
        Mark the tree and its associated objects as not present.
        """
        self.present = False
        self.save()
        for audit_trail_record in self.history.all():
            audit_trail_record.present = False
            audit_trail_record.save()

    def __unicode__(self):
        if self.species:
            return u'%s, %s, %s' % (self.species.common_name or '', self.species.scientific_name, self.plot.geocoded_address)
        else:
            return self.plot.geocoded_address

status_types = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
)

class Pending(models.Model):
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)
    text_value = models.CharField(max_length=255, blank=True, null=True)
    submitted = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, related_name="pend_submitted_by")
    status = models.CharField(max_length=10, choices=status_types)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, related_name="pend_updated_by")

    # These properties make 'django sorting' work
    # they really shouldn't be needed...?
    @property
    def species(self):
        if self.tree:
            return self.tree.species
        else:
            return None

    @property
    def address_street(self):
        if self.tree:
            return self.tree.address_street
        else:
            return None

    def set_create_attributes(self, user, field_name, field_value):
        self.field = field_name
        self.value = field_value
        self.submitted_by = user
        self.status = 'pending'
        self.updated_by = user

        if  field_name in settings.CHOICES:
            for choice_key, choice_value in settings.CHOICES[field_name]:
                if str(choice_key) == str(field_value):
                    self.text_value = choice_value
                    break

    def approve(self, updating_user):
        if self.status != 'pending':
            raise ValidationError('The Pending instance is not in the "pending" status and cannot be approved.')
        self.updated_by = updating_user
        self.status = 'approved'
        self.save()

    def reject(self, updating_user):
        if self.status != 'pending':
            raise ValidationError('The Pending instance is not in the "pending" status and cannot be rejected.')
        self.status = 'rejected'
        self.updated_by = updating_user
        self.save()

class TreePending(Pending):
    tree = models.ForeignKey(Tree)

    def _approve(self, updating_user):
        super(TreePending, self).approve(updating_user)
        update = {}
        update['old_' + self.field] = getattr(self.tree, self.field).__str__()
        update[self.field] = self.value.__str__()

        setattr(self.tree, self.field, self.value)
        self.tree.last_updated_by = self.submitted_by
        self.tree._audit_diff = simplejson.dumps(update)
        self.tree.save()

    def set_create_attributes(self, user, field_name, field_value):
        super(TreePending, self).set_create_attributes(user, field_name, field_value)
        if field_name == 'species_id':
            self.text_value = Species.objects.get(id=field_value).scientific_name

    @transaction.commit_on_success
    def approve_and_reject_other_active_pends_for_the_same_field(self, updating_user):
        self._approve(updating_user)
        for active_pend in self.tree.get_active_pends():
            if active_pend != self and active_pend.field == self.field:
                active_pend.reject(updating_user)

class PlotPending(Pending):
    plot = models.ForeignKey(Plot)

    geometry = models.PointField(srid=4326, blank=True, null=True)
    objects = models.GeoManager()

    @property
    def tree(self):
        return self.plot.current_tree()

    def _approve(self, updating_user):
        super(PlotPending, self).approve(updating_user)
        update = {}
        if self.geometry:
            update['old_geometry'] = simplejson.loads(self.plot.geometry.geojson)
            update['geometry'] = simplejson.loads(self.geometry.geojson)
            self.plot.geometry = self.geometry
        else:
            update['old_' + self.field] = getattr(self.plot, self.field).__str__()
            update[self.field] = self.value.__str__()
            setattr(self.plot, self.field, self.value)

        self.plot.last_updated_by = self.submitted_by
        self.plot._audit_diff = simplejson.dumps(update)
        self.plot.save()

    def set_create_attributes(self, user, field_name, field_value):
        super(PlotPending, self).set_create_attributes(user, field_name, field_value)
        if field_name == 'geometry':
            self.geometry = field_value
        else:
            # Omit the geometry so that PlotPending.approve will use the text value
            self.geometry = None

    @transaction.commit_on_success
    def approve_and_reject_other_active_pends_for_the_same_field(self, updating_user):
        self._approve(updating_user)
        for active_pend in self.plot.get_active_pends():
            if active_pend != self and active_pend.field == self.field:
                active_pend.reject(updating_user)

class TreeWatch(models.Model):
    key = models.CharField(max_length=255, choices=watch_choices.iteritems())
    value = models.CharField(max_length=255)
    tree = models.ForeignKey(Tree)
    severity = models.IntegerField(default=0)
    valid = models.BooleanField(default=False)

class TreeFavorite(FavoriteBase):
    tree = models.ForeignKey(Tree)

class Stewardship(models.Model):
    performed_by = models.ForeignKey(User)
    performed_date = models.DateTimeField()

    @classmethod
    def thing_with_activities(clazz, actions, idfld):
        count = len(actions)
        actions = ",".join(["'%s'" % z for z in actions])

        from django.db import connection, transaction
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT %(tree_or_plot)s_id
            FROM treemap_%(tree_or_plot)sstewardship
            WHERE activity in ( %(activities)s )
            GROUP BY %(tree_or_plot)s_id
            HAVING COUNT(DISTINCT activity) = %(count)d
            """ % {
                "tree_or_plot": idfld,
                "activities": actions,
                "count": count
            })

        return [k[0] for k in cursor.fetchall()]

    @classmethod
    def trees_with_activities(clazz, actions):
        return Stewardship.thing_with_activities(actions, "tree")

    @classmethod
    def plots_with_activities(clazz, actions):
        return Stewardship.thing_with_activities(actions, "plot")

    class Meta:
        ordering = ["performed_date"]

class TreeStewardship(Stewardship):
    activity = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["tree_stewardship"])
    tree = models.ForeignKey(Tree)

    def get_activity(self):
        for key, value in settings.CHOICES["tree_stewardship"]:
            if key == self.activity:
                return value
        return None

class PlotStewardship(Stewardship):
    activity = models.CharField(max_length=256, null=True, blank=True, choices=settings.CHOICES["plot_stewardship"])
    plot = models.ForeignKey(Plot)

    def get_activity(self):
        for key, value in settings.CHOICES["plot_stewardship"]:
            if key == self.activity:
                return value
        return None

class TreeItem(models.Model):
    """
    generic model for TreeAlert, TreeAction, and TreeStatus.  Classes
    inheriting from here should have a "key" charField with a set of choices
    and a 'value' field which might be a Float (boolean would be 0.0 or 1.0) or a DateTime, depending
    """
    reported = models.DateTimeField(auto_now=True)
    reported_by = models.ForeignKey(User)
    tree = models.ForeignKey(Tree)
    comment = models.TextField(blank=True)

    class Meta:
        abstract=True

    def validate_all(self):
        if self.tree:
            return self.tree.validate_all()

    def __unicode__(self):
        return u'%s, %s, %s' % (self.reported, self.tree, self.key)

def get_parent_id(instance):
    return instance.key

class TreeFlags(TreeItem):
    key = models.CharField(max_length=256, choices=settings.CHOICES["projects"])
    value = models.DateTimeField(auto_now=True)


class TreePhoto(TreeItem):
    def get_photo_path(instance, filename):
        test_path = os.path.join(settings.SITE_ROOT, settings.MEDIA_ROOT, 'photos', str(instance.tree_id), filename)
        extra = 1
        while os.path.exists(test_path):
           extra += 1
           test_path = os.path.join(settings.SITE_ROOT, settings.MEDIA_ROOT, 'photos', str(instance.tree_id), str(extra) + '_' + filename)
        path = os.path.join('photos', str(instance.tree_id), str(extra) + '_' + filename)
        return path

    title = models.CharField(max_length=256,null=True,blank=True)
    photo = ImageField(upload_to=get_photo_path)


    def save(self,*args,**kwargs):
        super(TreeItem, self).save(*args,**kwargs)
        self.tree._audit_diff = '{"new photo": "' + self.title + '"}'
        self.tree.save()

    def __unicode__(self):
        return u'%s, %s, %s' % (self.reported, self.tree, self.title)


class TreeAlert(TreeItem):
    """
    status of attributes that we want to track changes over time.
    sidwalk damage might be scale of 0 thru 5, where dbh or height might be an arbitrary float
    """
    key = models.CharField(max_length=256, choices=settings.CHOICES["alerts"])
    value = models.DateTimeField()
    solved = models.BooleanField(default=False)

#Should be removed in favor of stewardship activities
class TreeAction(TreeItem):
    key = models.CharField(max_length=256, choices=settings.CHOICES["actions"])
    value = models.DateTimeField()

class ResourceSummaryModel(models.Model):
    annual_stormwater_management = models.FloatField(help_text="gallons")
    annual_electricity_conserved = models.FloatField(help_text="kWh")
    annual_energy_conserved = models.FloatField(help_text="kWh")
    annual_natural_gas_conserved = models.FloatField(help_text="kWh")
    annual_air_quality_improvement = models.FloatField(help_text="lbs")
    annual_co2_sequestered = models.FloatField(help_text="lbs")
    annual_co2_avoided = models.FloatField(help_text="lbs")
    annual_co2_reduced = models.FloatField(help_text="lbs")
    total_co2_stored = models.FloatField(help_text="lbs")
    annual_ozone = models.FloatField(help_text="lbs")
    annual_nox = models.FloatField(help_text="lbs")
    annual_pm10 = models.FloatField(help_text="lbs")
    annual_sox = models.FloatField(help_text="lbs")
    annual_voc = models.FloatField(help_text="lbs")
    annual_bvoc = models.FloatField(help_text="lbs")


    def benefits(self):
        d = {}
        b = BenefitValues.objects.all()[0]
        d['water'] = (self.annual_stormwater_management * b.stormwater)

        d['energy'] = (self.annual_energy_conserved * b.electricity)

        d['air_quality'] = abs((self.annual_ozone * b.ozone) \
                            + (self.annual_nox * b.nox) \
                            + (self.annual_pm10 * b.pm10) \
                            + (self.annual_sox * b.sox) \
                            + (self.annual_voc * b.voc) \
                            + (self.annual_bvoc * b.bvoc)
                            )

        d['natural_gas'] = self.annual_natural_gas_conserved * b.natural_gas
        d['co2_reduced'] = (self.annual_co2_sequestered * b.co2) + (self.annual_co2_avoided * b.co2)
        d['co2_stored'] = self.total_co2_stored * b.co2
        d['greenhouse'] = (self.annual_co2_sequestered + self.annual_co2_avoided) * b.co2

        return d

    def total_benefit(self):
        b = self.benefits()
        return b['water'] + b['energy'] + b['air_quality'] + b['greenhouse']

    def get_benefits(self):
        benefits = self.benefits()
        benefits['total'] = self.total_benefit()
        return benefits


class TreeResource(ResourceSummaryModel):
    """
    resource results for a specific tree.  should get updated whenever a tree does.
    """
    tree = models.OneToOneField(Tree, primary_key=True)
    def __unicode__(self): return u'%s' % (self.tree)


class AggregateSummaryModel(ResourceSummaryModel):
    last_updated = models.DateTimeField(auto_now=True)
    total_trees = models.IntegerField()
    total_plots = models.IntegerField()
    #distinct_species = models.IntegerField()

    def ensure_recent(self, current_tree_count = 0):
      if current_tree_count == self.total_trees and (datetime.now() - self.last_updated).seconds < 7200:
          return True

      self.delete()
      return False

# to cache large searches via GET params
class AggregateSearchResult(AggregateSummaryModel):
    key = models.CharField(max_length=256,unique=True)

class AggregateNeighborhood(AggregateSummaryModel):
    location = models.OneToOneField(Neighborhood, related_name='aggregates')

class AggregateSupervisorDistrict(AggregateSummaryModel):
    location = models.OneToOneField(SupervisorDistrict, related_name='aggregates')

class AggregateZipCode(AggregateSummaryModel):
    location = models.OneToOneField(ZipCode, related_name='aggregates')

#import meta_badges
