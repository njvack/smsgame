# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'OutgoingTextMessage.phone_number'
        db.delete_column('sampler_outgoingtextmessage', 'phone_number')

        # Deleting field 'OutgoingTextMessage.tropo_json'
        db.delete_column('sampler_outgoingtextmessage', 'tropo_json')


    def backwards(self, orm):
        
        # Adding field 'OutgoingTextMessage.phone_number'
        db.add_column('sampler_outgoingtextmessage', 'phone_number', self.gf('sampler.models.PhoneNumberField')(default=0, max_length=255), keep_default=False)

        # Adding field 'OutgoingTextMessage.tropo_json'
        db.add_column('sampler_outgoingtextmessage', 'tropo_json', self.gf('django.db.models.fields.TextField')(default=0), keep_default=False)


    models = {
        'sampler.experiencesample': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'ExperienceSample'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'negative_emotion': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']"}),
            'positive_emotion': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
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
        'sampler.gamepermission': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'GamePermission'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']"}),
            'permissed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.hilowgame': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'HiLowGame'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'correct_guess': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guessed_low': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']"}),
            'result_reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.incomingtextmessage': {
            'Meta': {'object_name': 'IncomingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']", 'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'max_length': '255'}),
            'tropo_json': ('django.db.models.fields.TextField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.outgoingtextmessage': {
            'Meta': {'object_name': 'OutgoingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']", 'null': 'True', 'blank': 'True'}),
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
            'status': ('django.db.models.fields.CharField', [], {'default': "'sleeping'", 'max_length': '20'}),
            'stopped': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.taskday': {
            'Meta': {'unique_together': "(('participant', 'task_day'),)", 'object_name': 'TaskDay'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'earliest_contact': ('django.db.models.fields.DateTimeField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(22, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_game_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latest_contact': ('django.db.models.fields.DateTimeField', [], {}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Participant']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(8, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'waiting'", 'max_length': '255'}),
            'task_day': ('django.db.models.fields.DateField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sampler']
