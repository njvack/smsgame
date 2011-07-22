# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'IncomingTextMessage.phone_number'
        db.alter_column('sampler_incomingtextmessage', 'phone_number', self.gf('sampler.models.PhoneNumberField')(max_length=255))

        # Changing field 'Participant.phone_number'
        db.alter_column('sampler_participant', 'phone_number', self.gf('sampler.models.PhoneNumberField')(unique=True, max_length=255))

        # Adding field 'Experiment.max_messages_per_day'
        db.add_column('sampler_experiment', 'max_messages_per_day', self.gf('django.db.models.fields.IntegerField')(default=35), keep_default=False)

        # Adding field 'Experiment.min_time_between_samples'
        db.add_column('sampler_experiment', 'min_time_between_samples', self.gf('django.db.models.fields.IntegerField')(default=60), keep_default=False)

        # Adding field 'Experiment.max_time_between_samples'
        db.add_column('sampler_experiment', 'max_time_between_samples', self.gf('django.db.models.fields.IntegerField')(default=90), keep_default=False)

        # Adding field 'Experiment.response_window'
        db.add_column('sampler_experiment', 'response_window', self.gf('django.db.models.fields.IntegerField')(default=420), keep_default=False)

        # Adding field 'Experiment.game_value'
        db.add_column('sampler_experiment', 'game_value', self.gf('django.db.models.fields.DecimalField')(default=20.0, max_digits=5, decimal_places=2), keep_default=False)

        # Adding field 'Experiment.participation_value'
        db.add_column('sampler_experiment', 'participation_value', self.gf('django.db.models.fields.DecimalField')(default=25.0, max_digits=5, decimal_places=2), keep_default=False)

        # Adding field 'Experiment.bonus_value'
        db.add_column('sampler_experiment', 'bonus_value', self.gf('django.db.models.fields.DecimalField')(default=40.0, max_digits=5, decimal_places=2), keep_default=False)

        # Adding field 'Experiment.min_pct_answered_for_bonus'
        db.add_column('sampler_experiment', 'min_pct_answered_for_bonus', self.gf('django.db.models.fields.IntegerField')(default=90), keep_default=False)

        # Changing field 'OutgoingTextMessage.phone_number'
        db.alter_column('sampler_outgoingtextmessage', 'phone_number', self.gf('sampler.models.PhoneNumberField')(max_length=255))


    def backwards(self, orm):
        
        # Changing field 'IncomingTextMessage.phone_number'
        db.alter_column('sampler_incomingtextmessage', 'phone_number', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Participant.phone_number'
        db.alter_column('sampler_participant', 'phone_number', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True))

        # Deleting field 'Experiment.max_messages_per_day'
        db.delete_column('sampler_experiment', 'max_messages_per_day')

        # Deleting field 'Experiment.min_time_between_samples'
        db.delete_column('sampler_experiment', 'min_time_between_samples')

        # Deleting field 'Experiment.max_time_between_samples'
        db.delete_column('sampler_experiment', 'max_time_between_samples')

        # Deleting field 'Experiment.response_window'
        db.delete_column('sampler_experiment', 'response_window')

        # Deleting field 'Experiment.game_value'
        db.delete_column('sampler_experiment', 'game_value')

        # Deleting field 'Experiment.participation_value'
        db.delete_column('sampler_experiment', 'participation_value')

        # Deleting field 'Experiment.bonus_value'
        db.delete_column('sampler_experiment', 'bonus_value')

        # Deleting field 'Experiment.min_pct_answered_for_bonus'
        db.delete_column('sampler_experiment', 'min_pct_answered_for_bonus')

        # Changing field 'OutgoingTextMessage.phone_number'
        db.alter_column('sampler_outgoingtextmessage', 'phone_number', self.gf('django.db.models.fields.CharField')(max_length=255))


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
            'Meta': {'object_name': 'TaskDay'},
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
