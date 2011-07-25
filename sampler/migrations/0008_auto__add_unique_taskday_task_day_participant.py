# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'TaskDay', fields ['task_day', 'participant']
        db.create_unique('sampler_taskday', ['task_day', 'participant_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TaskDay', fields ['task_day', 'participant']
        db.delete_unique('sampler_taskday', ['task_day', 'participant_id'])


    models = {
        'sampler.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'bonus_value': ('django.db.models.fields.DecimalField', [], {'default': '40.0', 'max_digits': '5', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day_count': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'game_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'game_value': ('django.db.models.fields.DecimalField', [], {'default': '20.0', 'max_digits': '5', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_messages_per_day': ('django.db.models.fields.IntegerField', [], {'default': '35'}),
            'max_time_between_samples': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'min_pct_answered_for_bonus': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'min_time_between_samples': ('django.db.models.fields.IntegerField', [], {'default': '60'}),
            'participation_value': ('django.db.models.fields.DecimalField', [], {'default': '25.0', 'max_digits': '5', 'decimal_places': '2'}),
            'response_window': ('django.db.models.fields.IntegerField', [], {'default': '420'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.incomingtextmessage': {
            'Meta': {'object_name': 'IncomingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']", 'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'max_length': '255'}),
            'tropo_json': ('django.db.models.fields.TextField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.outgoingtextmessage': {
            'Meta': {'object_name': 'OutgoingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']", 'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'max_length': '255'}),
            'tropo_json': ('django.db.models.fields.TextField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.participant': {
            'Meta': {'object_name': 'Participant'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_contact_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'unique': 'True', 'max_length': '255'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "('waiting', 'Waiting to run')", 'max_length': '20'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.taskday': {
            'Meta': {'unique_together': "(('participant', 'task_day'),)", 'object_name': 'TaskDay'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': "'22:00'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_game_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': "'8:00'"}),
            'task_day': ('django.db.models.fields.DateField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sampler']
