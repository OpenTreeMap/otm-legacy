# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TreeRegionPolygon'
        db.create_table('polygons_treeregionpolygon', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('region_id', self.gf('django.db.models.fields.FloatField')()),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal('polygons', ['TreeRegionPolygon'])

        # Adding model 'DBHClass'
        db.create_table('polygons_dbhclass', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('dbh_min', self.gf('django.db.models.fields.FloatField')()),
            ('dbh_max', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('polygons', ['DBHClass'])

        # Adding model 'TreeRegionEntry'
        db.create_table('polygons_treeregionentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polygon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['polygons.TreeRegionPolygon'])),
            ('species', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treemap.Species'])),
            ('dbhclass', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['polygons.DBHClass'])),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('polygons', ['TreeRegionEntry'])


    def backwards(self, orm):
        # Deleting model 'TreeRegionPolygon'
        db.delete_table('polygons_treeregionpolygon')

        # Deleting model 'DBHClass'
        db.delete_table('polygons_dbhclass')

        # Deleting model 'TreeRegionEntry'
        db.delete_table('polygons_treeregionentry')


    models = {
        'polygons.dbhclass': {
            'Meta': {'object_name': 'DBHClass'},
            'dbh_max': ('django.db.models.fields.FloatField', [], {}),
            'dbh_min': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'polygons.treeregionentry': {
            'Meta': {'object_name': 'TreeRegionEntry'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'dbhclass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polygons.DBHClass']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polygon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polygons.TreeRegionPolygon']"}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Species']"})
        },
        'polygons.treeregionpolygon': {
            'Meta': {'object_name': 'TreeRegionPolygon'},
            'geometry': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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