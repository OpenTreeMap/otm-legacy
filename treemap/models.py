import os
import math
from decimal import *
from datetime import datetime
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Sum
from django.contrib.gis.measure import D
from django.contrib.auth.models import User, Group
from sorl.thumbnail.fields import ImageWithThumbnailsField
from classfaves.models import FavoriteBase
import logging
import audit

RESOURCE_NAMES = ['Hydro interception',
                     'Property Value',
                     'AQ Ozone dep',
                     'AQ NOx dep',
                     'AQ PM10 dep',
                     'AQ SOx dep',
                     'AQ NOx avoided',
                     'AQ PM10 avoided',
                     'AQ SOx avoided',
                     'AQ VOC avoided',
                     'BVOC',
                     'Net VOCs',
                     'CO2 sequestered',
                     'CO2 Decomp',
                     'CO2 Maint',
                     'Net CO2 sequestered',
                     'CO2 avoided',
                     'Natural Gas',
                     'Electricity',
                     'LSA',
                     'CPA',
                     'CO2 Storage']


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
    
    def __unicode__(self): return '%s' % (self.area)

class Choices(models.Model):
    field = models.CharField(max_length=255, choices=choices_choices)
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=255)
    key_type = models.CharField(max_length=15)
    
    def get_field_choices(self, fieldName):
        li = {}
        for c in Choices.objects.filter(field__exact=fieldName):

            if c.key_type == 'int':
                key =  int(c.key)
            elif c.key_type == 'bool':
                if c.key == 'True':
                    key = True
                else:
                    key = False
            elif c.key_type == 'str':
                key =  c.key
            elif c.key_type == 'none':
                key =  None
            else:
                raise Exception("Invalid key type %r" % c.key_type)

            #TODO: Figure out why we need both! The 2. works for status, 1. for all else
            li[c.key] = c.value
            #if key is not None:
                #li[key] = c.value
        return li.items()
    
    def __unicode__(self): return '%s(%s) - %s' % (self.field, self.key, self.value)
        
choices = Choices()
    
STATUS_CHOICES = {
        "sidewalk_damage": Choices().get_field_choices('sidewalk_damage'),
        "plot_type": Choices().get_field_choices('plot'),
        "powerline_conflict_potential": choices.get_field_choices('bool_set'),
        "condition": Choices().get_field_choices('condition'),
        "canopy_condition": Choices().get_field_choices('canopy_condition'),
    }

# GEOGRAPHIES #
class Neighborhood(models.Model):
    """
    from zillow
    """
    name = models.CharField(max_length=255)
    region_id = models.IntegerField()
    city = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()
    
    def __unicode__(self): return '%s' % self.name
 

class SupervisorDistrict(models.Model):
    """
    from sfgov
    """
    id = models.IntegerField(primary_key=True)
    supervisor = models.CharField(max_length=255)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()
    
    def __unicode__(self): return '%s (%s)' % (self.id, self.supervisor)

    
class ZipCode(models.Model):
    """
    from sfgov
    """
    zip = models.CharField(max_length=255)
    geometry = models.MultiPolygonField(srid=4326)
    objects=models.GeoManager()
    
    def __unicode__(self): return '%s (%s)' % (self.id, self.zip)
    
    
class Factoid(models.Model):
    category = models.CharField(max_length=255, choices=Choices().get_field_choices('factoid'))
    header = models.CharField(max_length=100)
    fact = models.TextField(max_length=500)
    
    def __unicode__(self): return '%s: %s' % (self.category, self.fact)


class Resource(models.Model):
    """
    For use in STRATUM - a Resource can have many species,
    and has different values for each dbh/resource combo.
    """
    meta_species = models.CharField(max_length=150)
    region = models.CharField(max_length=150)
    hydro_interception_dbh = models.TextField()
    property_value_dbh = models.TextField()
    aq_ozone_dep_dbh = models.TextField()
    aq_nox_dep_dbh = models.TextField()
    aq_pm10_dep_dbh = models.TextField()
    aq_sox_dep_dbh = models.TextField()
    aq_nox_avoided_dbh = models.TextField()
    aq_pm10_avoided_dbh = models.TextField()
    aq_sox_avoided_dbh = models.TextField()
    aq_voc_avoided_dbh = models.TextField()
    bvoc_dbh = models.TextField()
    net_vocs_dbh = models.TextField()
    co2_sequestered_dbh = models.TextField()
    co2_decomp_dbh = models.TextField()
    co2_maint_dbh = models.TextField()
    net_co2_sequestered_dbh = models.TextField()
    co2_avoided_dbh = models.TextField()
    natural_gas_dbh = models.TextField()
    electricity_dbh = models.TextField()
    lsa_dbh = models.TextField()
    cpa_dbh = models.TextField()
    dbh_by_age_class_dbh = models.TextField()
    co2_storage_dbh = models.TextField()
    objects = models.GeoManager()
    
    def get_interpolated_location(self, dbh):
        """
        return how far along we are along the dbh_list, and interpolated %
        """
        dbh_list = [3.81,11.43,22.86,38.10,53.34,68.58,83.82,99.06,114.30]
        #convert from cm to inches
        dbh_list = [d * 0.393700787 for d in dbh_list]

        if dbh < dbh_list[0]:
            return[1,0]
        if dbh >= dbh_list[-1]:
            return[len(dbh_list)-1,1]
        for i, d in enumerate(dbh_list):
            if dbh < d:
                interp_between = (float(dbh - dbh_list[i-1]) / float(dbh_list[i] - dbh_list[i-1]))
                #return length_along + (interp_between * 1.0/(len(dbh_list)-1))
                return i, interp_between
                
    def calc_resource_summaries(self, br):
        summaries = {}
        summaries['annual_stormwater_management'] = br['hydro_interception_dbh'] * 264.1
        summaries['annual_electricity_conserved'] = br['electricity_dbh']
        # http://sftrees.securemaps.com/ticket/25#comment:7
        summaries['annual_natural_gas_conserved'] = br['natural_gas_dbh'] * 0.293
        summaries['annual_air_quality_improvement'] = (
            br['aq_ozone_dep_dbh'] + 
            br['aq_nox_dep_dbh'] + 
            br['aq_pm10_dep_dbh'] +
            br['aq_sox_dep_dbh'] +
            br['aq_nox_avoided_dbh'] +
            br['aq_pm10_avoided_dbh'] +
            br['aq_sox_avoided_dbh'] +
            br['aq_voc_avoided_dbh'] +
            br['bvoc_dbh']) * 2.2
        summaries['annual_ozone'] = br['aq_ozone_dep_dbh'] * 2.2
        summaries['annual_nox'] = br['aq_nox_dep_dbh'] * 2.2
        summaries['annual_pm10'] = br['aq_pm10_dep_dbh'] * 2.2
        summaries['annual_sox'] = br['aq_sox_dep_dbh'] * 2.2
        summaries['annual_voc'] = br['aq_voc_avoided_dbh'] * 2.2
        summaries['annual_bvoc'] = br['bvoc_dbh'] * 2.2
        summaries['annual_co2_sequestered'] = br['co2_sequestered_dbh'] * 2.2
        summaries['annual_co2_avoided'] = br['co2_avoided_dbh'] * 2.2
        summaries['annual_co2_reduced'] = (br['co2_sequestered_dbh'] + br['co2_avoided_dbh']) * 2.2
        summaries['total_co2_stored'] = br['co2_storage_dbh'] * 2.2
        summaries['annual_energy_conserved'] = br['electricity_dbh'] + br['natural_gas_dbh'] * 0.293
        return summaries

    def calc_base_resources(self, resource_list, dbh):
        """
        example: treeobject.species.resource_species.calc_base_resources(['Electricity'], 36.2)
        """
        index, interp = self.get_interpolated_location(dbh)
        
        #print 'idx,interp',index, interp
        results = {}
        for resource in resource_list:
            #print 'resrc' , resource
            fname = "%s_dbh" % resource.lower().replace(' ','_')
            #get two values of interest - TODO FIX for sketchy eval
            dbhs= (eval(getattr(self, fname)))
            #start at same list index as dbh_list, and figure out what interp value is here
            local_interp = float(dbhs[index] - dbhs[index-1]) * interp 
            #print 'local_interp', local_interp
            results[fname] = dbhs[index-1] + local_interp
            #print results[resource]
        return results
        
    def __unicode__(self): return '%s' % (self.meta_species)
    
    
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
    accepted_symbol = models.CharField(max_length=255, null=True, blank=True)
    synonym_symbol = models.CharField(max_length=255, null=True, blank=True)
    symbol = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255)
    genus = models.CharField(max_length=255)
    species = models.CharField(max_length=255, null=True, blank=True) #sometimes we just have genus/cultivar combo
    common_name = models.CharField(max_length=255, null=True, blank=True)
    cultivar_name = models.CharField(max_length=255, null=True, blank=True)

    #plants_floristic_area = models.CharField(max_length=255, null=True, blank=True)
    #state_and_province = models.CharField(max_length=455, null=True, blank=True)
    #growth_habit = models.CharField(max_length=255, null=True, blank=True) #tree/shrub
    native_status = models.CharField(max_length=255, null=True, blank=True)
    #federal_noxious_status = models.CharField(max_length=255, null=True, blank=True)
    #state_noxious_status = models.CharField(max_length=255, null=True, blank=True)
    #invasive = models.CharField(max_length=255, null=True, blank=True)
    #federal_t_e_status = models.CharField(max_length=255, null=True, blank=True)
    #state_t_e_status = models.CharField(max_length=255, null=True, blank=True)
    #national_wetland_indicator_status = models.CharField(max_length=255, null=True, blank=True)
    #regional_wetland_indicator_status = models.CharField(max_length=255, null=True, blank=True)
    fall_conspicuous = models.NullBooleanField(choices=choices.get_field_choices('bool_set'))
    #fire_resistance = models.NullBooleanField(choices=choices.get_field_choices('bool_set'))
    flower_conspicuous = models.NullBooleanField()
    #bloom_period = models.CharField(max_length=255, null=True, blank=True)
    #fruit_seed_abundance = models.CharField(max_length=255, null=True, blank=True)
    #fruit_seed_period_begin = models.CharField(max_length=255, null=True, blank=True)
    #fruit_seed_period_end = models.CharField(max_length=255, null=True, blank=True)
    #berry_nut_seed_product = models.NullBooleanField(choices=choices.get_field_choices('bool_set'))
    palatable_human = models.NullBooleanField(choices=choices.get_field_choices('bool_set'))
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
        if not self.scientific_name:
            if self.genus and self.species:
                self.scientific_name = '%s %s' % (self.genus, self.species)
        super(Species, self).save(*args,**kwargs)  
    
    def __unicode__(self):
        if self.cultivar_name:
            return "%s, '%s'" % (self.common_name,self.cultivar_name)
        else:
            return '%s' % (self.common_name)
    
    
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

class Tree(models.Model):
    def __init__(self, *args, **kwargs):
        super(Tree, self).__init__(*args, **kwargs)  #save, in order to get ID for the tree
        #self.current_geometry = self.geometry or None       
    #owner properties based on wiki/DatabaseQuestions
    data_owner = models.ForeignKey(User, related_name="owner", null=True)
    tree_owner = models.CharField(max_length=256, null=True, blank=True)
    steward_name = models.CharField(max_length=256, null=True, blank=True) #only modifyable by admin
    steward_user = models.OneToOneField(User, null=True, blank=True) #only modifyable by admin
    sponsor = models.CharField(max_length=256, null=True, blank=True) #only modifyable by us
    
    #original data to help owners associate back to their own db
    owner_orig_id = models.CharField(max_length=256, null=True, blank=True)
    owner_additional_properties = models.TextField(null=True, blank=True, help_text = "Additional Properties (not searchable)")

    species = models.ForeignKey(Species,verbose_name="Scientific name",null=True, blank=True)
    orig_species = models.CharField(max_length=256, null=True, blank=True)
    #special = models.BooleanField(help_text="Landmark or other Special status")
    current_dbh = models.FloatField(null=True, blank=True) #gets auto-set on save
    date_planted = models.DateField(null=True, blank=True) 
    date_removed = models.DateField(null=True, blank=True)
    powerline_conflict_potential = models.NullBooleanField(
        help_text = "Are there overhead powerlines present?", 
        choices=choices.get_field_choices('bool_set'),null=True, blank=True)
    present = models.BooleanField(default=True)
    plot_width = models.IntegerField(null=True, blank=True)
    plot_length = models.IntegerField(null=True, blank=True) 
    plot_type = models.CharField(max_length=256, null=True, blank=True, choices=Choices().get_field_choices('plot'))
            
    address_street = models.CharField(max_length=256, blank=True, null=True)
    address_city = models.CharField(max_length=256, blank=True, null=True)
    address_zip = models.CharField(max_length=30,blank=True, null=True)
    neighborhood = models.ForeignKey(Neighborhood, null=True)
    zipcode = models.ForeignKey(ZipCode, null=True)
    
    geocoded_accuracy = models.IntegerField(null=True)
    geocoded_address = models.CharField(max_length=256)
    geocoded_lat = models.FloatField(null=True)
    geocoded_lon  = models.FloatField(null=True)

    geometry = models.PointField(srid=4326)
    geocoded_geometry = models.PointField(null=True, srid=4326)
    owner_geometry = models.PointField(null=True, srid=4326) #should we keep this?
   
    region = models.CharField(max_length=256)

    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='updated_by') # TODO set to current user
        
    s_order = models.IntegerField(null=True, blank=True)
   
    objects = models.GeoManager()
    history = audit.AuditTrail()
    
    import_event = models.ForeignKey(ImportEvent)
    
    
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
    
    def get_condition(self):
        condition = self.treestatus_set.filter(key='condition').order_by('-reported')
        if condition:
            return condition[0].display
        else:
            return None

    def get_sidewalk_damage(self,display=False):
        sidewalk_damage = self.treestatus_set.filter(key='sidewalk_damage').order_by('-reported')
        if sidewalk_damage:
            if display:
                return sidewalk_damage[0].display
            else:
                return sidewalk_damage[0].value
        else:
            return None

    def get_sidewalk_damage_display(self):
        return self.get_sidewalk_damage(display=True)
                
    def get_height(self):
        height = self.treestatus_set.filter(key='height').order_by('-reported')
        if height:
            return height[0].value
        else:
            return None
    
    def get_canopy_height(self):
        height = self.treestatus_set.filter(key='canopy_height').order_by('-reported')
        if height:
            return height[0].value
        else:
            return None     
            
    def get_canopy_condition(self):
        condition = self.treestatus_set.filter(key='canopy_condition').order_by('-reported')
        if condition:
            return condition[0].display
        else:
            return None    
            
    def update_dbh(self):
        #update the current_dbh if out of date .. called by treeStatus save
        if not self.current_dbh == self.get_dbh():
            self.current_dbh = self.get_dbh()
            self.save()
            
    def get_dbh(self):
        dbh = self.treestatus_set.filter(key='dbh').order_by('-reported')
        if dbh:
            return dbh[0].value
        else:
            return None
            
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
        
    def set_environmental_summaries(self):
        if not self.species or not self.current_dbh:
            logging.debug('no species or no dbh ..')
            return None
        tr =  TreeResource.objects.filter(tree=self)
        #check see if we have an existing tree resource
        if not tr:
            logging.debug('no tree resource for tree id %s' % self.id)
            if self.species.resource.all():
                logging.info(' but .. we do have a resource for species id %s; creating tr' % self.species.id)
                tr = TreeResource(tree=self)
            else:
                return None
        else:
            tr = tr[0]
        if not self.species.resource.all():
            #delete old TR if it exists
            tr.delete()
            return None
        #calc results and set them
        resource = self.species.resource.all()[0] #todo: and region
        base_resources = resource.calc_base_resources(RESOURCE_NAMES, self.current_dbh)
        results = resource.calc_resource_summaries(base_resources)
        if not results:
            logging.warning('Unable to calc results for %s, deleting TreeResource if it exists' % self)
            if tr.id:
                tr.delete()
            return None 
        #update summaries
        for k,v in results.items():
            setattr(tr, k, v)
            #print k, v
            #print getattr(tr,k)
        tr.save()
        logging.debug( 'tr saved.. tree id is %s' % (tr.tree.id))
        return True

    def is_complete(self):
        if self.species >= 0 and self.current_dbh:
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
        pnt = self.geometry
        n = Neighborhood.objects.filter(geometry__contains=pnt)
        z = ZipCode.objects.filter(geometry__contains=pnt)
        oldn = self.neighborhood
        oldz = self.zipcode
        
        if n: self.neighborhood = n[0]
        else: self.neighborhood = None
        if z: self.zipcode = z[0]
        else: self.zipcode = None
        
        super(Tree, self).save(*args,**kwargs) 
        
        self.set_environmental_summaries()
        #set new species counts
        if hasattr(self,'old_species') and self.old_species:
            self.old_species.save()
        if hasattr(self,'species') and self.species:
            self.species.save()
            
        if n and n[0] != oldn:        
            if n: self.update_aggregate(AggregateNeighborhood, n[0])
            if oldn: self.update_aggregate(AggregateNeighborhood, oldn)
        
        if z and z[0] != oldz:
            if z: self.update_aggregate(AggregateZipCode, z[0])
            if oldz: self.update_aggregate(AggregateZipCode, oldz)
        
    
    def quick_save(self,*args,**kwargs):
        super(Tree, self).save(*args,**kwargs) 
        self.set_environmental_summaries()
        #set new species counts
        if hasattr(self,'old_species') and self.old_species:
            self.old_species.save()
        if hasattr(self,'species') and self.species:
            self.species.save()
    
    def update_aggregate(self, ag_model, location):        
        agg =  ag_model.objects.filter(location=location)
        if agg:
            agg = agg[0]
        else:
            agg = ag_model(location=location)
        summaries = []        
        trees = Tree.objects.filter(geometry__within=location.geometry)
        agg.total_trees = len(trees)
        #TODO: speed this up! A lot!
        #agg.distinct_species = len(trees.values("species"))
        #TODO figure out how to summarize diff stratum stuff
        #field_names = [x.name for x in ResourceSummaryModel._meta.fields 
        #    if not x.name == 'id']
        #for f in field_names:
        #    fn = 'treeresource__' + f
        #    s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
        #    setattr(agg,f,s)
        agg.save()
        
    def percent_complete(self):
        has = 0
        desired = 6
        if self.species:
            if self.species.scientific_name:
                has += 1
        if self.get_condition():
            has += 1
        if self.get_sidewalk_damage():
            has += 1
        if not self.powerline_conflict_potential is None:
            has += 1
        if self.get_canopy_height():
            has += 1 
        if self.get_canopy_condition():
            has += 1
        attr = ['current_dbh','plot_width','plot_length','plot_type']
        desired += len(attr)
        for item in attr:
            if hasattr(self,item):
                if getattr(self,item):
                    has +=1
        return has/float(desired)*100
    
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
        if not self.geometry:
            return None
        nearby = Tree.objects.filter(geometry__distance_lte=(self.geometry, D(ft=10.0)))
        if nearby.count() > max_count: 
            if return_trees:
                return nearby 
            return (nearby.count()-max_count).__str__() #number greater than max_count allows
        return None
    
    
    # Disallowed combinations:
    #   Dead + 0% loss, Dead + 25% loss, Dead + 50% loss, Dead + 75% loss
    #   Excellent + 100% loss, Excellent + 75% loss
    def validate_canopy_condition(self):
        if not self.get_canopy_condition() or not self.get_condition():
            return None
        
        cond = self.get_condition()
        c_cond = self.get_canopy_condition()
        if cond == 'Dead':
            if not c_cond == 'Little or None (up to 100% missing)' and not c_cond == 'None' :
                return cond + ", " + c_cond
            
        elif cond == 'Excellent':
            if c_cond == 'Little or None (up to 100% missing)' or c_cond == 'Large Gaps (up to 75% missing)':
                return cond + ", " + c_cond
        
        return None
    
    # discussions: http://www.nativetreesociety.org/measure/tdi/diameter_height_ratio.htm
    def validate_height_dbh(self):
        if not self.get_height() or not self.get_dbh():
            return None
        getcontext().prec = 3
        cbh = self.get_dbh() * math.pi
        cbh_feet = cbh * .75 / 9
        float_ratio = self.get_height() / cbh_feet
        hd_ratio = Decimal(float_ratio.__str__())
        #print hd_ratio        
        if hd_ratio < 100:
            return None
        return round(hd_ratio, 2).__str__()
    
    def validate_max_dbh(self):
        if not self.get_dbh() or not self.species or not self.species.v_max_dbh:
            return None
        if self.get_dbh() > self.species.v_max_dbh:
            return self.get_dbh() + " (species max: " + self.species.v_max_dbh + ")"
        return None
        
    def validate_max_height(self):
        if not self.get_height() or not self.species or not self.species.v_max_height:
            return None
        if self.get_height() > self.species.v_max_height:
            return self.get_height() + " (species max: " + self.species.v_max_height + ")"
        return None
        
    def __unicode__(self): 
        if self.species:
            return '%s, %s, %s' % (self.species.common_name or '', self.species.scientific_name, self.geocoded_address)
        else:
            return self.geocoded_address    

class TreeWatch(models.Model):
    key = models.CharField(max_length=255, choices=watch_choices.iteritems())
    value = models.CharField(max_length=255)
    tree = models.ForeignKey(Tree)
    severity = models.IntegerField(default=0)
    valid = models.BooleanField(default=False)

class TreeFavorite(FavoriteBase):
    tree = models.ForeignKey(Tree)


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
        return '%s, %s, %s' % (self.reported, self.tree, self.key)

def get_parent_id(instance):
    return instance.key

class TreeFlags(TreeItem):
    key = models.CharField(max_length=256, choices=Choices().get_field_choices("local"))
    value = models.DateTimeField()

    history = audit.AuditTrail()

class TreePhoto(TreeItem):
    def get_photo_path(instance, filename):
        test_path = os.path.join(settings.MEDIA_ROOT, 'photos', str(instance.tree_id), filename)
        extra = 1
        while os.path.exists(test_path):
           extra += 1
           test_path = os.path.join(settings.MEDIA_ROOT, 'photos', str(instance.tree_id), str(extra) + '_' + filename)
        path = os.path.join('photos', str(instance.tree_id), str(extra) + '_' + filename)
        return path

    title = models.CharField(max_length=256,null=True,blank=True)
    photo = ImageWithThumbnailsField(upload_to=get_photo_path, blank=True, null=True, thumbnail={'size': (50, 50)})

    history = audit.AuditTrail()

    def __unicode__(self):
        return '%s, %s, %s' % (self.reported, self.tree, self.title)

        
class TreeAlert(TreeItem):
    """
    status of attributes that we want to track changes over time.
    sidwalk damage might be scale of 0 thru 5, where dbh or height might be an arbitrary float
    """
    key = models.CharField(max_length=256, choices=Choices().get_field_choices('alert'))
    value = models.DateTimeField()
    solved = models.BooleanField(default=False)    
    
    history = audit.AuditTrail()
    
class TreeAction(TreeItem): 
    key = models.CharField(max_length=256, choices=Choices().get_field_choices('action'))
    value = models.DateTimeField()

    history = audit.AuditTrail()
        
class TreeStatus(TreeItem):
    """
    status of attributes that we want to track changes over time.
    sidwalk damage might be scale of 0 thru 5, where dbh or height might be an arbitrary float
    """
    key = models.CharField(max_length=256, choices=status_choices)
    value = models.FloatField()

    history = audit.AuditTrail()
    
    @property
    def display(self):
        val = self.value
        if self.key in STATUS_CHOICES:
            choices = STATUS_CHOICES[self.key]
            for item in choices:
                if item[0] == self.value:
                    return item[1]
        return val

    
    def save(self,*args,**kwargs):
        #fix up tree if we got a new dbh
        self.tree.update_dbh()
        super(TreeStatus, self).save(*args,**kwargs) 

       
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
    def __unicode__(self): return '%s' % (self.tree)


class AggregateSummaryModel(ResourceSummaryModel):
    last_updated = models.DateTimeField(auto_now=True)
    total_trees = models.IntegerField()
    distinct_species = models.IntegerField()

    def ensure_recent(self, current_tree_count = ''):
      if current_tree_count and current_tree_count == self.total_trees:
          tm = True
      else:
          tm = False

      if tm and (datetime.now() - self.last_updated).seconds < 7200: #two hrs
          return True
      else:
          print 'deleting old cached object'
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
    
import meta_badges
