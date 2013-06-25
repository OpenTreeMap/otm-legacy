# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SpeciesImportEvent.field_order'
        db.add_column('importer_speciesimportevent', 'field_order',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'TreeImportEvent.field_order'
        db.add_column('importer_treeimportevent', 'field_order',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'SpeciesImportEvent.field_order'
        db.delete_column('importer_speciesimportevent', 'field_order')

        # Deleting field 'TreeImportEvent.field_order'
        db.delete_column('importer_treeimportevent', 'field_order')


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
        'importer.speciesimportevent': {
            'Meta': {'object_name': 'SpeciesImportEvent'},
            'commited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'errors': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'field_order': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'importer.speciesimportrow': {
            'Meta': {'object_name': 'SpeciesImportRow'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'errors': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idx': ('django.db.models.fields.IntegerField', [], {}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importer.SpeciesImportEvent']"}),
            'merged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Species']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '3'})
        },
        'importer.treeimportevent': {
            'Meta': {'object_name': 'TreeImportEvent'},
            'base_import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.ImportEvent']"}),
            'canopy_height_conversion_factor': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'commited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'completed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'diameter_conversion_factor': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'errors': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'field_order': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'plot_length_conversion_factor': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'plot_width_conversion_factor': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tree_height_conversion_factor': ('django.db.models.fields.FloatField', [], {'default': '1.0'})
        },
        'importer.treeimportrow': {
            'Meta': {'object_name': 'TreeImportRow'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'errors': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idx': ('django.db.models.fields.IntegerField', [], {}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['importer.TreeImportEvent']"}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treemap.Plot']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '3'})
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
        },
        'treemap.zipcode': {
            'Meta': {'object_name': 'ZipCode'},
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['importer']