# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Participant'
        db.create_table(u'sampler_participant', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Experiment'])),
            ('phone_number', self.gf('sampler.models.PhoneNumberField')(unique=True, max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='sleeping', max_length=20)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('next_contact_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('stopped', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'sampler', ['Participant'])

        # Adding model 'Experiment'
        db.create_table(u'sampler_experiment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('url_slug', self.gf('django.db.models.fields.SlugField')(default='pvhvsrtmzp', unique=True, max_length=50)),
            ('day_count', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('game_count', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('max_messages_per_day', self.gf('django.db.models.fields.IntegerField')(default=35)),
            ('min_time_between_samples', self.gf('django.db.models.fields.IntegerField')(default=60)),
            ('max_time_between_samples', self.gf('django.db.models.fields.IntegerField')(default=90)),
            ('response_window', self.gf('django.db.models.fields.IntegerField')(default=420)),
            ('game_value', self.gf('django.db.models.fields.DecimalField')(default=20.0, max_digits=5, decimal_places=2)),
            ('target_wins', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('target_losses', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('participation_value', self.gf('django.db.models.fields.DecimalField')(default=25.0, max_digits=5, decimal_places=2)),
            ('bonus_value', self.gf('django.db.models.fields.DecimalField')(default=4.0, max_digits=5, decimal_places=2)),
            ('min_pct_answered_for_bonus', self.gf('django.db.models.fields.IntegerField')(default=90)),
        ))
        db.send_create_signal(u'sampler', ['Experiment'])

        # Adding model 'ExperienceSample'
        db.create_table(u'sampler_experiencesample', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'])),
            ('incoming_text', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.IncomingTextMessage'], null=True, blank=True)),
            ('scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('answered_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('participant_status_when_sent', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('positive_emotion', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('negative_emotion', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'sampler', ['ExperienceSample'])

        # Adding model 'GamePermission'
        db.create_table(u'sampler_gamepermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'])),
            ('incoming_text', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.IncomingTextMessage'], null=True, blank=True)),
            ('scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('answered_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('participant_status_when_sent', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('permissed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'sampler', ['GamePermission'])

        # Adding model 'GuessingGame'
        db.create_table(u'sampler_guessinggame', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'])),
            ('incoming_text', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.IncomingTextMessage'], null=True, blank=True)),
            ('scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('answered_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('participant_status_when_sent', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('red_correct', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('guessed_red', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('result_reported_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'sampler', ['GuessingGame'])

        # Adding model 'TaskDay'
        db.create_table(u'sampler_taskday', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='waiting', max_length=255)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'])),
            ('task_day', self.gf('django.db.models.fields.DateField')()),
            ('start_time', self.gf('django.db.models.fields.TimeField')(default=datetime.time(8, 0))),
            ('end_time', self.gf('django.db.models.fields.TimeField')(default=datetime.time(22, 0))),
            ('earliest_contact', self.gf('django.db.models.fields.DateTimeField')()),
            ('latest_contact', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_game_day', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'sampler', ['TaskDay'])

        # Adding unique constraint on 'TaskDay', fields ['participant', 'task_day']
        db.create_unique(u'sampler_taskday', ['participant_id', 'task_day'])

        # Adding model 'IncomingTextMessage'
        db.create_table(u'sampler_incomingtextmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'], null=True, blank=True)),
            ('phone_number', self.gf('sampler.models.PhoneNumberField')(max_length=255)),
            ('message_text', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('tropo_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'sampler', ['IncomingTextMessage'])

        # Adding model 'OutgoingTextMessage'
        db.create_table(u'sampler_outgoingtextmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sampler.Participant'])),
            ('message_text', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'sampler', ['OutgoingTextMessage'])


    def backwards(self, orm):
        # Removing unique constraint on 'TaskDay', fields ['participant', 'task_day']
        db.delete_unique(u'sampler_taskday', ['participant_id', 'task_day'])

        # Deleting model 'Participant'
        db.delete_table(u'sampler_participant')

        # Deleting model 'Experiment'
        db.delete_table(u'sampler_experiment')

        # Deleting model 'ExperienceSample'
        db.delete_table(u'sampler_experiencesample')

        # Deleting model 'GamePermission'
        db.delete_table(u'sampler_gamepermission')

        # Deleting model 'GuessingGame'
        db.delete_table(u'sampler_guessinggame')

        # Deleting model 'TaskDay'
        db.delete_table(u'sampler_taskday')

        # Deleting model 'IncomingTextMessage'
        db.delete_table(u'sampler_incomingtextmessage')

        # Deleting model 'OutgoingTextMessage'
        db.delete_table(u'sampler_outgoingtextmessage')


    models = {
        u'sampler.experiencesample': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'ExperienceSample'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'negative_emotion': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'participant_status_when_sent': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'positive_emotion': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'bonus_value': ('django.db.models.fields.DecimalField', [], {'default': '4.0', 'max_digits': '5', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day_count': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'game_count': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'game_value': ('django.db.models.fields.DecimalField', [], {'default': '20.0', 'max_digits': '5', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_messages_per_day': ('django.db.models.fields.IntegerField', [], {'default': '35'}),
            'max_time_between_samples': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'min_pct_answered_for_bonus': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'min_time_between_samples': ('django.db.models.fields.IntegerField', [], {'default': '60'}),
            'participation_value': ('django.db.models.fields.DecimalField', [], {'default': '25.0', 'max_digits': '5', 'decimal_places': '2'}),
            'response_window': ('django.db.models.fields.IntegerField', [], {'default': '420'}),
            'target_losses': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'target_wins': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.SlugField', [], {'default': "'mccnfkmnzv'", 'unique': 'True', 'max_length': '50'})
        },
        u'sampler.gamepermission': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'GamePermission'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'participant_status_when_sent': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'permissed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.guessinggame': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'GuessingGame'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guessed_red': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'participant_status_when_sent': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'red_correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'result_reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.incomingtextmessage': {
            'Meta': {'object_name': 'IncomingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']", 'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'max_length': '255'}),
            'tropo_json': ('django.db.models.fields.TextField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.outgoingtextmessage': {
            'Meta': {'object_name': 'OutgoingTextMessage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_text': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.participant': {
            'Meta': {'object_name': 'Participant'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_contact_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'phone_number': ('sampler.models.PhoneNumberField', [], {'unique': 'True', 'max_length': '255'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'sleeping'", 'max_length': '20'}),
            'stopped': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.taskday': {
            'Meta': {'unique_together': "(('participant', 'task_day'),)", 'object_name': 'TaskDay'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'earliest_contact': ('django.db.models.fields.DateTimeField', [], {}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(22, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_game_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latest_contact': ('django.db.models.fields.DateTimeField', [], {}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(8, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'waiting'", 'max_length': '255'}),
            'task_day': ('django.db.models.fields.DateField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sampler']