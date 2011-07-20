# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Experiment'
        db.create_table('sampler_experiment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default=('active', 'Active'), max_length=20)),
            ('day_count', self.gf('django.db.models.fields.IntegerField')(default=7)),
            ('game_count', self.gf('django.db.models.fields.IntegerField')(default=5)),
        ))
        db.send_create_signal('sampler', ['Experiment'])

        # Deleting field 'Participant.game_count'
        db.delete_column('sampler_participant', 'game_count')

        # Deleting field 'Participant.day_count'
        db.delete_column('sampler_participant', 'day_count')

        # Adding field 'Participant.experiment'
        db.add_column('sampler_participant', 'experiment', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['sampler.Experiment']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Experiment'
        db.delete_table('sampler_experiment')

        # Adding field 'Participant.game_count'
        db.add_column('sampler_participant', 'game_count', self.gf('django.db.models.fields.IntegerField')(default=5), keep_default=False)

        # Adding field 'Participant.day_count'
        db.add_column('sampler_participant', 'day_count', self.gf('django.db.models.fields.IntegerField')(default=7), keep_default=False)

        # Deleting field 'Participant.experiment'
        db.delete_column('sampler_participant', 'experiment_id')


    models = {
        'sampler.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day_count': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'game_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "('active', 'Active')", 'max_length': '20'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'sampler.participant': {
            'Meta': {'object_name': 'Participant'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sampler.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_contact_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
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
