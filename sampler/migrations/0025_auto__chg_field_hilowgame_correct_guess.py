# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'HiLowGame.correct_guess'
        db.alter_column(u'sampler_hilowgame', 'correct_guess', self.gf('django.db.models.fields.IntegerField')(null=True))
        db.alter_column(u'sampler_hilowgame', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True))
        db.alter_column(u'sampler_experiencesample', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True))
        db.alter_column(u'sampler_gamepermission', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')(null=True))

    def backwards(self, orm):

        # Changing field 'HiLowGame.correct_guess'
        db.alter_column(u'sampler_gamepermission', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')())
        db.alter_column(u'sampler_experiencesample', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')())
        db.alter_column(u'sampler_hilowgame', 'scheduled_at', self.gf('django.db.models.fields.DateTimeField')())
        db.alter_column(u'sampler_hilowgame', 'correct_guess', self.gf('django.db.models.fields.IntegerField')())

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
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'bonus_value': ('django.db.models.fields.DecimalField', [], {'default': '4.0', 'max_digits': '5', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'day_count': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'game_count': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
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
            'url_slug': ('django.db.models.fields.SlugField', [], {'default': "'vjtdqcfszn'", 'unique': 'True', 'max_length': '50'})
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
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'sampler.hilowgame': {
            'Meta': {'ordering': "['-scheduled_at']", 'object_name': 'HiLowGame'},
            'answered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'correct_guess': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guessed_low': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_text': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.IncomingTextMessage']", 'null': 'True', 'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sampler.Participant']"}),
            'participant_status_when_sent': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'result_reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'scheduled_at': ('django.db.models.fields.DateTimeField', [], {}),
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