# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TreeRegionEntryAudit'
        db.create_table('polygons_treeregionentry_audit', (
            ('_audit_user_rep', self.gf('django.db.models.fields.IntegerField')()),
            ('_audit_diff', self.gf('django.db.models.fields.TextField')()),
            ('_audit_verified', self.gf('django.db.models.fields.IntegerField')()),
            ('polygon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_treeregionentry', to=orm['polygons.TreeRegionPolygon'])),
            ('species', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_treeregionentry', to=orm['treemap.Species'])),
            ('dbhclass', self.gf('django.db.models.fields.related.ForeignKey')(related_name='_audit_treeregionentry', to=orm['polygons.DBHClass'])),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_treeregionentry_updated_by', null=True, to=orm['auth.User'])),
            ('_audit_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_audit_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('_audit_change_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('polygons', ['TreeRegionEntryAudit'])

        # Adding model 'TreeRegionPolygonAudit'
        db.create_table('polygons_treeregionpolygon_audit', (
            ('_audit_user_rep', self.gf('django.db.models.fields.IntegerField')()),
            ('_audit_diff', self.gf('django.db.models.fields.TextField')()),
            ('_audit_verified', self.gf('django.db.models.fields.IntegerField')()),
            ('region_id', self.gf('django.db.models.fields.FloatField')()),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('last_updated_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='_audit_treeregionpolygon_updated_by', null=True, to=orm['auth.User'])),
            ('_audit_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_audit_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('_audit_change_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('polygons', ['TreeRegionPolygonAudit'])

        # Adding field 'TreeRegionEntry.last_updated'
        db.add_column('polygons_treeregionentry', 'last_updated',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'TreeRegionEntry.last_updated_by'
        db.add_column('polygons_treeregionentry', 'last_updated_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='treeregionentry_updated_by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'TreeRegionPolygon.last_updated'
        db.add_column('polygons_treeregionpolygon', 'last_updated',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'TreeRegionPolygon.last_updated_by'
        db.add_column('polygons_treeregionpolygon', 'last_updated_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='treeregionpolygon_updated_by', null=True, to=orm['auth.User']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'TreeRegionEntryAudit'
        db.delete_table('polygons_treeregionentry_audit')

        # Deleting model 'TreeRegionPolygonAudit'
        db.delete_table('polygons_treeregionpolygon_audit')

        # Deleting field 'TreeRegionEntry.last_updated'
        db.delete_column('polygons_treeregionentry', 'last_updated')

        # Deleting field 'TreeRegionEntry.last_updated_by'
        db.delete_column('polygons_treeregionentry', 'last_updated_by_id')

        # Deleting field 'TreeRegionPolygon.last_updated'
        db.delete_column('polygons_treeregionpolygon', 'last_updated')

        # Deleting field 'TreeRegionPolygon.last_updated_by'
        db.delete_column('polygons_treeregionpolygon', 'last_updated_by_id')


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
        'polygons.dbhclass': {
            'Meta': {'object_name': 'DBHClass'},
            'dbh_max': ('django.db.models.fields.FloatField', [], {}),
            'dbh_min': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'polygons.treeregionentry': {
            'Meta': {'object_name': 'TreeRegionEntry'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'dbhclass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polygons.DBHClass']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'treeregionentry_updated_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'polygon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polygons.TreeRegionPolygon']"}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Species']"})
        },
        'polygons.treeregionentryaudit': {
            'Meta': {'ordering': "['-_audit_timestamp']", 'object_name': 'TreeRegionEntryAudit', 'db_table': "'polygons_treeregionentry_audit'"},
            '_audit_change_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            '_audit_diff': ('django.db.models.fields.TextField', [], {}),
            '_audit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            '_audit_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            '_audit_user_rep': ('django.db.models.fields.IntegerField', [], {}),
            '_audit_verified': ('django.db.models.fields.IntegerField', [], {}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'dbhclass': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_treeregionentry'", 'to': "orm['polygons.DBHClass']"}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_treeregionentry_updated_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'polygon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_treeregionentry'", 'to': "orm['polygons.TreeRegionPolygon']"}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_audit_treeregionentry'", 'to': "orm['treemap.Species']"})
        },
        'polygons.treeregionpolygon': {
            'Meta': {'object_name': 'TreeRegionPolygon'},
            'geometry': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'treeregionpolygon_updated_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'region_id': ('django.db.models.fields.FloatField', [], {})
        },
        'polygons.treeregionpolygonaudit': {
            'Meta': {'ordering': "['-_audit_timestamp']", 'object_name': 'TreeRegionPolygonAudit', 'db_table': "'polygons_treeregionpolygon_audit'"},
            '_audit_change_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            '_audit_diff': ('django.db.models.fields.TextField', [], {}),
            '_audit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            '_audit_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            '_audit_user_rep': ('django.db.models.fields.IntegerField', [], {}),
            '_audit_verified': ('django.db.models.fields.IntegerField', [], {}),
            'geometry': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'last_updated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_audit_treeregionpolygon_updated_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'region_id': ('django.db.models.fields.FloatField', [], {})
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
            'other_part_of_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
        }
    }

    complete_apps = ['polygons']