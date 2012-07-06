# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BenefitValues'
        db.create_table('treemap_benefitvalues', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('stormwater', self.gf('django.db.models.fields.FloatField')()),
            ('electricity', self.gf('django.db.models.fields.FloatField')()),
            ('natural_gas', self.gf('django.db.models.fields.FloatField')()),
            ('co2', self.gf('django.db.models.fields.FloatField')()),
            ('ozone', self.gf('django.db.models.fields.FloatField')()),
            ('nox', self.gf('django.db.models.fields.FloatField')()),
            ('pm10', self.gf('django.db.models.fields.FloatField')()),
            ('sox', self.gf('django.db.models.fields.FloatField')()),
            ('voc', self.gf('django.db.models.fields.FloatField')()),
            ('bvoc', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('treemap', ['BenefitValues'])

        # Adding model 'CommentFlag'
        db.create_table('treemap_commentflag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('flagged', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('flagged_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comment_flags', to=orm['threadedcomments.ThreadedComment'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('treemap', ['CommentFlag'])

        # Adding model 'Neighborhood'
        db.create_table('treemap_neighborhood', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('region_id', self.gf('django.db.models.fields.IntegerField')()),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('county', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
        ))
        db.send_create_signal('treemap', ['Neighborhood'])

        # Adding model 'SupervisorDistrict'
        db.create_table('treemap_supervisordistrict', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('supervisor', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
        ))
        db.send_create_signal('treemap', ['SupervisorDistrict'])

        # Adding model 'ZipCode'
        db.create_table('treemap_zipcode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
        ))
        db.send_create_signal('treemap', ['ZipCode'])

        # Adding model 'ExclusionMask'
        db.create_table('treemap_exclusionmask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['ExclusionMask'])

        # Adding model 'Factoid'
        db.create_table('treemap_factoid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('header', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('fact', self.gf('django.db.models.fields.TextField')(max_length=500)),
        ))
        db.send_create_signal('treemap', ['Factoid'])

        # Adding model 'Resource'
        db.create_table('treemap_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('meta_species', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('hydro_interception_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_ozone_dep_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_nox_dep_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_pm10_dep_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_sox_dep_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_nox_avoided_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_pm10_avoided_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_sox_avoided_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aq_voc_avoided_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bvoc_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('co2_sequestered_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('co2_avoided_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('natural_gas_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('electricity_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('co2_storage_dbh', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['Resource'])

        # Adding model 'Species'
        db.create_table('treemap_species', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('symbol', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('alternate_symbol', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('itree_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('genus', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('species', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('cultivar_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('common_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('native_status', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('bloom_period', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('fruit_period', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('fall_conspicuous', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('flower_conspicuous', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('palatable_human', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('wildlife_value', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('fact_sheet', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
            ('plant_guide', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
            ('tree_count', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('v_max_dbh', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('v_max_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('v_multiple_trunks', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['Species'])

        # Adding M2M table for field resource on 'Species'
        db.create_table('treemap_species_resource', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('species', models.ForeignKey(orm['treemap.species'], null=False)),
            ('resource', models.ForeignKey(orm['treemap.resource'], null=False))
        ))
        db.create_unique('treemap_species_resource', ['species_id', 'resource_id'])

        # Adding model 'GeocodeCache'
        db.create_table('treemap_geocodecache', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('geocoded_address', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('geocoded_lat', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('geocoded_lon', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('geocoded_accuracy', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('geocoded_geometry', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
        ))
        db.send_create_signal('treemap', ['GeocodeCache'])

        # Adding model 'ImportEvent'
        db.create_table('treemap_importevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('import_date', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['ImportEvent'])

        # Adding model 'PlotAudit'
        db.create_table('treemap_plot_audit', (
            ('_audit_user_rep', self.gf('django.db.models.fields.IntegerField')()),
            ('_audit_diff', self.gf('django.db.models.fields.TextField')()),
            ('_audit_verified', self.gf('django.db.models.fields.IntegerField')()),
            ('present', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('width', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('length', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('powerline_conflict_potential', self.gf('django.db.models.fields.CharField')(default='3', max_length=256, null=True, blank=True)),
            ('sidewalk_damage', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_city', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_zip', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('neighborhoods', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('zipcode', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_plot', null=True, to=orm['treemap.ZipCode'])),
            ('geocoded_accuracy', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geocoded_address', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('geocoded_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('geocoded_lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_plot_updated_by', to=orm['auth.User'])),
            ('import_event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_plot', to=orm['treemap.ImportEvent'])),
            ('data_owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_owner', null=True, to=orm['auth.User'])),
            ('owner_orig_id', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('owner_additional_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('owner_additional_properties', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('_audit_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_audit_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('_audit_change_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('treemap', ['PlotAudit'])

        # Adding model 'Plot'
        db.create_table('treemap_plot', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('present', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('width', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('length', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('powerline_conflict_potential', self.gf('django.db.models.fields.CharField')(default='3', max_length=256, null=True, blank=True)),
            ('sidewalk_damage', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_city', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('address_zip', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('neighborhoods', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('zipcode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.ZipCode'], null=True, blank=True)),
            ('geocoded_accuracy', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geocoded_address', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('geocoded_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('geocoded_lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PointField')()),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plot_updated_by', to=orm['auth.User'])),
            ('import_event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.ImportEvent'])),
            ('data_owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owner', null=True, to=orm['auth.User'])),
            ('owner_orig_id', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('owner_additional_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('owner_additional_properties', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('treemap', ['Plot'])

        # Adding M2M table for field neighborhood on 'Plot'
        db.create_table('treemap_plot_neighborhood', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('plot', models.ForeignKey(orm['treemap.plot'], null=False)),
            ('neighborhood', models.ForeignKey(orm['treemap.neighborhood'], null=False))
        ))
        db.create_unique('treemap_plot_neighborhood', ['plot_id', 'neighborhood_id'])

        # Adding model 'TreeAudit'
        db.create_table('treemap_tree_audit', (
            ('_audit_user_rep', self.gf('django.db.models.fields.IntegerField')()),
            ('_audit_diff', self.gf('django.db.models.fields.TextField')()),
            ('_audit_verified', self.gf('django.db.models.fields.IntegerField')()),
            ('plot', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_tree', to=orm['treemap.Plot'])),
            ('tree_owner', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('steward_name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('steward_user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_steward', null=True, to=orm['auth.User'])),
            ('sponsor', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('species', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_tree', null=True, to=orm['treemap.Species'])),
            ('species_other1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('species_other2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('orig_species', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('dbh', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('canopy_height', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('date_planted', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('date_removed', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('present', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_updated_by', to=orm['auth.User'])),
            ('s_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('photo_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('projects', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('import_event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_tree', to=orm['treemap.ImportEvent'])),
            ('condition', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('canopy_condition', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('_audit_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_audit_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('_audit_change_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('treemap', ['TreeAudit'])

        # Adding model 'Tree'
        db.create_table('treemap_tree', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plot', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Plot'])),
            ('tree_owner', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('steward_name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('steward_user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='steward', null=True, to=orm['auth.User'])),
            ('sponsor', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('species', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Species'], null=True, blank=True)),
            ('species_other1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('species_other2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('orig_species', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('dbh', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('canopy_height', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('date_planted', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('date_removed', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('present', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='updated_by', to=orm['auth.User'])),
            ('s_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('photo_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('projects', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('import_event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.ImportEvent'])),
            ('condition', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('canopy_condition', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('treemap', ['Tree'])

        # Adding model 'Pending'
        db.create_table('treemap_pending', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('text_value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('submitted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('submitted_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pend_submitted_by', to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pend_updated_by', to=orm['auth.User'])),
        ))
        db.send_create_signal('treemap', ['Pending'])

        # Adding model 'TreePending'
        db.create_table('treemap_treepending', (
            ('pending_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.Pending'], unique=True, primary_key=True)),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
        ))
        db.send_create_signal('treemap', ['TreePending'])

        # Adding model 'PlotPending'
        db.create_table('treemap_plotpending', (
            ('pending_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.Pending'], unique=True, primary_key=True)),
            ('plot', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Plot'])),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['PlotPending'])

        # Adding model 'TreeWatch'
        db.create_table('treemap_treewatch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
            ('severity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('valid', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('treemap', ['TreeWatch'])

        # Adding model 'TreeFavorite'
        db.create_table('treemap_treefavorite', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
        ))
        db.send_create_signal('treemap', ['TreeFavorite'])

        # Adding model 'Stewardship'
        db.create_table('treemap_stewardship', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('performed_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('performed_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('treemap', ['Stewardship'])

        # Adding model 'TreeStewardship'
        db.create_table('treemap_treestewardship', (
            ('stewardship_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.Stewardship'], unique=True, primary_key=True)),
            ('activity', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
        ))
        db.send_create_signal('treemap', ['TreeStewardship'])

        # Adding model 'PlotStewardship'
        db.create_table('treemap_plotstewardship', (
            ('stewardship_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.Stewardship'], unique=True, primary_key=True)),
            ('activity', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('plot', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Plot'])),
        ))
        db.send_create_signal('treemap', ['PlotStewardship'])

        # Adding model 'TreeFlags'
        db.create_table('treemap_treeflags', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reported', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('reported_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('treemap', ['TreeFlags'])

        # Adding model 'TreePhoto'
        db.create_table('treemap_treephoto', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reported', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('reported_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('photo', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
        ))
        db.send_create_signal('treemap', ['TreePhoto'])

        # Adding model 'TreeAlert'
        db.create_table('treemap_treealert', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reported', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('reported_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.DateTimeField')()),
            ('solved', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('treemap', ['TreeAlert'])

        # Adding model 'TreeAction'
        db.create_table('treemap_treeaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reported', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('reported_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Tree'])),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('treemap', ['TreeAction'])

        # Adding model 'ResourceSummaryModel'
        db.create_table('treemap_resourcesummarymodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('annual_stormwater_management', self.gf('django.db.models.fields.FloatField')()),
            ('annual_electricity_conserved', self.gf('django.db.models.fields.FloatField')()),
            ('annual_energy_conserved', self.gf('django.db.models.fields.FloatField')()),
            ('annual_natural_gas_conserved', self.gf('django.db.models.fields.FloatField')()),
            ('annual_air_quality_improvement', self.gf('django.db.models.fields.FloatField')()),
            ('annual_co2_sequestered', self.gf('django.db.models.fields.FloatField')()),
            ('annual_co2_avoided', self.gf('django.db.models.fields.FloatField')()),
            ('annual_co2_reduced', self.gf('django.db.models.fields.FloatField')()),
            ('total_co2_stored', self.gf('django.db.models.fields.FloatField')()),
            ('annual_ozone', self.gf('django.db.models.fields.FloatField')()),
            ('annual_nox', self.gf('django.db.models.fields.FloatField')()),
            ('annual_pm10', self.gf('django.db.models.fields.FloatField')()),
            ('annual_sox', self.gf('django.db.models.fields.FloatField')()),
            ('annual_voc', self.gf('django.db.models.fields.FloatField')()),
            ('annual_bvoc', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('treemap', ['ResourceSummaryModel'])

        # Adding model 'TreeResource'
        db.create_table('treemap_treeresource', (
            ('resourcesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.ResourceSummaryModel'], unique=True)),
            ('tree', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.Tree'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('treemap', ['TreeResource'])

        # Adding model 'AggregateSummaryModel'
        db.create_table('treemap_aggregatesummarymodel', (
            ('resourcesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.ResourceSummaryModel'], unique=True, primary_key=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('total_trees', self.gf('django.db.models.fields.IntegerField')()),
            ('total_plots', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('treemap', ['AggregateSummaryModel'])

        # Adding model 'AggregateSearchResult'
        db.create_table('treemap_aggregatesearchresult', (
            ('aggregatesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.AggregateSummaryModel'], unique=True, primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
        ))
        db.send_create_signal('treemap', ['AggregateSearchResult'])

        # Adding model 'AggregateNeighborhood'
        db.create_table('treemap_aggregateneighborhood', (
            ('aggregatesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.AggregateSummaryModel'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.OneToOneField')(related_name='aggregates', unique=True, to=orm['treemap.Neighborhood'])),
        ))
        db.send_create_signal('treemap', ['AggregateNeighborhood'])

        # Adding model 'AggregateSupervisorDistrict'
        db.create_table('treemap_aggregatesupervisordistrict', (
            ('aggregatesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.AggregateSummaryModel'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.OneToOneField')(related_name='aggregates', unique=True, to=orm['treemap.SupervisorDistrict'])),
        ))
        db.send_create_signal('treemap', ['AggregateSupervisorDistrict'])

        # Adding model 'AggregateZipCode'
        db.create_table('treemap_aggregatezipcode', (
            ('aggregatesummarymodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['treemap.AggregateSummaryModel'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.OneToOneField')(related_name='aggregates', unique=True, to=orm['treemap.ZipCode'])),
        ))
        db.send_create_signal('treemap', ['AggregateZipCode'])


    def backwards(self, orm):
        # Deleting model 'BenefitValues'
        db.delete_table('treemap_benefitvalues')

        # Deleting model 'CommentFlag'
        db.delete_table('treemap_commentflag')

        # Deleting model 'Neighborhood'
        db.delete_table('treemap_neighborhood')

        # Deleting model 'SupervisorDistrict'
        db.delete_table('treemap_supervisordistrict')

        # Deleting model 'ZipCode'
        db.delete_table('treemap_zipcode')

        # Deleting model 'ExclusionMask'
        db.delete_table('treemap_exclusionmask')

        # Deleting model 'Factoid'
        db.delete_table('treemap_factoid')

        # Deleting model 'Resource'
        db.delete_table('treemap_resource')

        # Deleting model 'Species'
        db.delete_table('treemap_species')

        # Removing M2M table for field resource on 'Species'
        db.delete_table('treemap_species_resource')

        # Deleting model 'GeocodeCache'
        db.delete_table('treemap_geocodecache')

        # Deleting model 'ImportEvent'
        db.delete_table('treemap_importevent')

        # Deleting model 'PlotAudit'
        db.delete_table('treemap_plot_audit')

        # Deleting model 'Plot'
        db.delete_table('treemap_plot')

        # Removing M2M table for field neighborhood on 'Plot'
        db.delete_table('treemap_plot_neighborhood')

        # Deleting model 'TreeAudit'
        db.delete_table('treemap_tree_audit')

        # Deleting model 'Tree'
        db.delete_table('treemap_tree')

        # Deleting model 'Pending'
        db.delete_table('treemap_pending')

        # Deleting model 'TreePending'
        db.delete_table('treemap_treepending')

        # Deleting model 'PlotPending'
        db.delete_table('treemap_plotpending')

        # Deleting model 'TreeWatch'
        db.delete_table('treemap_treewatch')

        # Deleting model 'TreeFavorite'
        db.delete_table('treemap_treefavorite')

        # Deleting model 'Stewardship'
        db.delete_table('treemap_stewardship')

        # Deleting model 'TreeStewardship'
        db.delete_table('treemap_treestewardship')

        # Deleting model 'PlotStewardship'
        db.delete_table('treemap_plotstewardship')

        # Deleting model 'TreeFlags'
        db.delete_table('treemap_treeflags')

        # Deleting model 'TreePhoto'
        db.delete_table('treemap_treephoto')

        # Deleting model 'TreeAlert'
        db.delete_table('treemap_treealert')

        # Deleting model 'TreeAction'
        db.delete_table('treemap_treeaction')

        # Deleting model 'ResourceSummaryModel'
        db.delete_table('treemap_resourcesummarymodel')

        # Deleting model 'TreeResource'
        db.delete_table('treemap_treeresource')

        # Deleting model 'AggregateSummaryModel'
        db.delete_table('treemap_aggregatesummarymodel')

        # Deleting model 'AggregateSearchResult'
        db.delete_table('treemap_aggregatesearchresult')

        # Deleting model 'AggregateNeighborhood'
        db.delete_table('treemap_aggregateneighborhood')

        # Deleting model 'AggregateSupervisorDistrict'
        db.delete_table('treemap_aggregatesupervisordistrict')

        # Deleting model 'AggregateZipCode'
        db.delete_table('treemap_aggregatezipcode')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'threadedcomments.threadedcomment': {
            'Meta': {'ordering': "('-date_submitted',)", 'object_name': 'ThreadedComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'date_approved': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'markup': ('django.db.models.fields.IntegerField', [], {'default': '5', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'blank': 'True', 'to': "orm['threadedcomments.ThreadedComment']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'treemap.aggregateneighborhood': {
            'Meta': {'object_name': 'AggregateNeighborhood', '_ormbases': ['treemap.AggregateSummaryModel']},
            'aggregatesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.AggregateSummaryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'aggregates'", 'unique': 'True', 'to': "orm['treemap.Neighborhood']"})
        },
        'treemap.aggregatesearchresult': {
            'Meta': {'object_name': 'AggregateSearchResult', '_ormbases': ['treemap.AggregateSummaryModel']},
            'aggregatesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.AggregateSummaryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        },
        'treemap.aggregatesummarymodel': {
            'Meta': {'object_name': 'AggregateSummaryModel', '_ormbases': ['treemap.ResourceSummaryModel']},
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'resourcesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.ResourceSummaryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'total_plots': ('django.db.models.fields.IntegerField', [], {}),
            'total_trees': ('django.db.models.fields.IntegerField', [], {})
        },
        'treemap.aggregatesupervisordistrict': {
            'Meta': {'object_name': 'AggregateSupervisorDistrict', '_ormbases': ['treemap.AggregateSummaryModel']},
            'aggregatesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.AggregateSummaryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'aggregates'", 'unique': 'True', 'to': "orm['treemap.SupervisorDistrict']"})
        },
        'treemap.aggregatezipcode': {
            'Meta': {'object_name': 'AggregateZipCode', '_ormbases': ['treemap.AggregateSummaryModel']},
            'aggregatesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.AggregateSummaryModel']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'aggregates'", 'unique': 'True', 'to': "orm['treemap.ZipCode']"})
        },
        'treemap.benefitvalues': {
            'Meta': {'object_name': 'BenefitValues'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'bvoc': ('django.db.models.fields.FloatField', [], {}),
            'co2': ('django.db.models.fields.FloatField', [], {}),
            'electricity': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'natural_gas': ('django.db.models.fields.FloatField', [], {}),
            'nox': ('django.db.models.fields.FloatField', [], {}),
            'ozone': ('django.db.models.fields.FloatField', [], {}),
            'pm10': ('django.db.models.fields.FloatField', [], {}),
            'sox': ('django.db.models.fields.FloatField', [], {}),
            'stormwater': ('django.db.models.fields.FloatField', [], {}),
            'voc': ('django.db.models.fields.FloatField', [], {})
        },
        'treemap.commentflag': {
            'Meta': {'object_name': 'CommentFlag'},
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comment_flags'", 'to': "orm['threadedcomments.ThreadedComment']"}),
            'flagged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flagged_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'treemap.exclusionmask': {
            'Meta': {'object_name': 'ExclusionMask'},
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'treemap.factoid': {
            'Meta': {'object_name': 'Factoid'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fact': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'header': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'treemap.geocodecache': {
            'Meta': {'object_name': 'GeocodeCache'},
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'geocoded_accuracy': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'geocoded_address': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'geocoded_geometry': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'geocoded_lat': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'geocoded_lon': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'treemap.importevent': {
            'Meta': {'object_name': 'ImportEvent'},
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_date': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'treemap.neighborhood': {
            'Meta': {'object_name': 'Neighborhood'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'county': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'region_id': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'treemap.pending': {
            'Meta': {'object_name': 'Pending'},
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pend_submitted_by'", 'to': "orm['auth.User']"}),
            'text_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pend_updated_by'", 'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'treemap.plot': {
            'Meta': {'object_name': 'Plot'},
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'data_owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owner'", 'null': 'True', 'to': "orm['auth.User']"}),
            'geocoded_accuracy': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geocoded_address': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'geocoded_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geocoded_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.ImportEvent']"}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plot_updated_by'", 'to': "orm['auth.User']"}),
            'length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'neighborhood': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['treemap.Neighborhood']", 'null': 'True', 'symmetrical': 'False'}),
            'neighborhoods': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'owner_additional_properties': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner_orig_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'owner_additional_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'powerline_conflict_potential': ('django.db.models.fields.CharField', [], {'default': "'3'", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'present': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sidewalk_damage': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.ZipCode']", 'null': 'True', 'blank': 'True'})
        },
        'treemap.plotaudit': {
            'Meta': {'ordering': "['-_audit_timestamp']", 'object_name': 'PlotAudit', 'db_table': "'treemap_plot_audit'"},
            '_audit_change_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            '_audit_diff': ('django.db.models.fields.TextField', [], {}),
            '_audit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            '_audit_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            '_audit_user_rep': ('django.db.models.fields.IntegerField', [], {}),
            '_audit_verified': ('django.db.models.fields.IntegerField', [], {}),
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'data_owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_owner'", 'null': 'True', 'to': "orm['auth.User']"}),
            'geocoded_accuracy': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'geocoded_address': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'geocoded_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geocoded_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_plot'", 'to': "orm['treemap.ImportEvent']"}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_plot_updated_by'", 'to': "orm['auth.User']"}),
            'length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'neighborhoods': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'owner_additional_properties': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner_orig_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'owner_additional_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'powerline_conflict_potential': ('django.db.models.fields.CharField', [], {'default': "'3'", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'present': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sidewalk_damage': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_plot'", 'null': 'True', 'to': "orm['treemap.ZipCode']"})
        },
        'treemap.plotpending': {
            'Meta': {'object_name': 'PlotPending', '_ormbases': ['treemap.Pending']},
            'geometry': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'pending_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.Pending']", 'unique': 'True', 'primary_key': 'True'}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Plot']"})
        },
        'treemap.plotstewardship': {
            'Meta': {'object_name': 'PlotStewardship', '_ormbases': ['treemap.Stewardship']},
            'activity': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Plot']"}),
            'stewardship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.Stewardship']", 'unique': 'True', 'primary_key': 'True'})
        },
        'treemap.resource': {
            'Meta': {'object_name': 'Resource'},
            'aq_nox_avoided_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_nox_dep_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_ozone_dep_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_pm10_avoided_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_pm10_dep_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_sox_avoided_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_sox_dep_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'aq_voc_avoided_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bvoc_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'co2_avoided_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'co2_sequestered_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'co2_storage_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'electricity_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hydro_interception_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_species': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'natural_gas_dbh': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'})
        },
        'treemap.resourcesummarymodel': {
            'Meta': {'object_name': 'ResourceSummaryModel'},
            'annual_air_quality_improvement': ('django.db.models.fields.FloatField', [], {}),
            'annual_bvoc': ('django.db.models.fields.FloatField', [], {}),
            'annual_co2_avoided': ('django.db.models.fields.FloatField', [], {}),
            'annual_co2_reduced': ('django.db.models.fields.FloatField', [], {}),
            'annual_co2_sequestered': ('django.db.models.fields.FloatField', [], {}),
            'annual_electricity_conserved': ('django.db.models.fields.FloatField', [], {}),
            'annual_energy_conserved': ('django.db.models.fields.FloatField', [], {}),
            'annual_natural_gas_conserved': ('django.db.models.fields.FloatField', [], {}),
            'annual_nox': ('django.db.models.fields.FloatField', [], {}),
            'annual_ozone': ('django.db.models.fields.FloatField', [], {}),
            'annual_pm10': ('django.db.models.fields.FloatField', [], {}),
            'annual_sox': ('django.db.models.fields.FloatField', [], {}),
            'annual_stormwater_management': ('django.db.models.fields.FloatField', [], {}),
            'annual_voc': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'total_co2_stored': ('django.db.models.fields.FloatField', [], {})
        },
        'treemap.species': {
            'Meta': {'object_name': 'Species'},
            'alternate_symbol': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'bloom_period': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cultivar_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fact_sheet': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fall_conspicuous': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'flower_conspicuous': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'fruit_period': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'genus': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'itree_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'native_status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'palatable_human': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'plant_guide': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'resource': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['treemap.Resource']", 'null': 'True', 'symmetrical': 'False'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'species': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tree_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'v_max_dbh': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v_max_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'v_multiple_trunks': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'wildlife_value': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'treemap.stewardship': {
            'Meta': {'object_name': 'Stewardship'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'performed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'performed_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'treemap.supervisordistrict': {
            'Meta': {'object_name': 'SupervisorDistrict'},
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'supervisor': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'treemap.tree': {
            'Meta': {'object_name': 'Tree'},
            'canopy_condition': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'canopy_height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'condition': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'date_planted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dbh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.ImportEvent']"}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'updated_by'", 'to': "orm['auth.User']"}),
            'orig_species': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'photo_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Plot']"}),
            'present': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'projects': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            's_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Species']", 'null': 'True', 'blank': 'True'}),
            'species_other1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'species_other2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sponsor': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'steward_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'steward_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'steward'", 'null': 'True', 'to': "orm['auth.User']"}),
            'tree_owner': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'treemap.treeaction': {
            'Meta': {'object_name': 'TreeAction'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'reported': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"}),
            'value': ('django.db.models.fields.DateTimeField', [], {})
        },
        'treemap.treealert': {
            'Meta': {'object_name': 'TreeAlert'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'reported': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"}),
            'value': ('django.db.models.fields.DateTimeField', [], {})
        },
        'treemap.treeaudit': {
            'Meta': {'ordering': "['-_audit_timestamp']", 'object_name': 'TreeAudit', 'db_table': "'treemap_tree_audit'"},
            '_audit_change_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            '_audit_diff': ('django.db.models.fields.TextField', [], {}),
            '_audit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            '_audit_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            '_audit_user_rep': ('django.db.models.fields.IntegerField', [], {}),
            '_audit_verified': ('django.db.models.fields.IntegerField', [], {}),
            'canopy_condition': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'canopy_height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'condition': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'date_planted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dbh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_tree'", 'to': "orm['treemap.ImportEvent']"}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_updated_by'", 'to': "orm['auth.User']"}),
            'orig_species': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'photo_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_tree'", 'to': "orm['treemap.Plot']"}),
            'present': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'projects': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            's_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_tree'", 'null': 'True', 'to': "orm['treemap.Species']"}),
            'species_other1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'species_other2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sponsor': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'steward_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'steward_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_steward'", 'null': 'True', 'to': "orm['auth.User']"}),
            'tree_owner': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'treemap.treefavorite': {
            'Meta': {'object_name': 'TreeFavorite'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'treemap.treeflags': {
            'Meta': {'object_name': 'TreeFlags'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'reported': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"}),
            'value': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'treemap.treepending': {
            'Meta': {'object_name': 'TreePending', '_ormbases': ['treemap.Pending']},
            'pending_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.Pending']", 'unique': 'True', 'primary_key': 'True'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"})
        },
        'treemap.treephoto': {
            'Meta': {'object_name': 'TreePhoto'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'reported': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"})
        },
        'treemap.treeresource': {
            'Meta': {'object_name': 'TreeResource', '_ormbases': ['treemap.ResourceSummaryModel']},
            'resourcesummarymodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.ResourceSummaryModel']", 'unique': 'True'}),
            'tree': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.Tree']", 'unique': 'True', 'primary_key': 'True'})
        },
        'treemap.treestewardship': {
            'Meta': {'object_name': 'TreeStewardship', '_ormbases': ['treemap.Stewardship']},
            'activity': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'stewardship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['treemap.Stewardship']", 'unique': 'True', 'primary_key': 'True'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"})
        },
        'treemap.treewatch': {
            'Meta': {'object_name': 'TreeWatch'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'severity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Tree']"}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'treemap.zipcode': {
            'Meta': {'object_name': 'ZipCode'},
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['treemap']