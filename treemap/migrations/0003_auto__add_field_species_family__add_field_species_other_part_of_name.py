# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Species.family'
        db.add_column('treemap_species', 'family',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Species.other_part_of_name'
        db.add_column('treemap_species', 'other_part_of_name',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Species.family'
        db.delete_column('treemap_species', 'family')

        # Deleting field 'Species.other_part_of_name'
        db.delete_column('treemap_species', 'other_part_of_name')


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
            'owner_additional_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner_additional_properties': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner_orig_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'powerline_conflict_potential': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
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
            'owner_additional_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner_additional_properties': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner_orig_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'powerline_conflict_potential': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
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
            'Meta': {'ordering': "['performed_date']", 'object_name': 'PlotStewardship', '_ormbases': ['treemap.Stewardship']},
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
            'family': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'flower_conspicuous': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'fruit_period': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'genus': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'itree_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'native_status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'other_part_of_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
            'Meta': {'ordering': "['performed_date']", 'object_name': 'Stewardship'},
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
            'pests': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
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
            'tree_owner': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
            'pests': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
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
            'tree_owner': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
            'Meta': {'ordering': "['performed_date']", 'object_name': 'TreeStewardship', '_ormbases': ['treemap.Stewardship']},
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