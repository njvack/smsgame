from django.contrib import admin
from . import models


class ExperimentAdmin(admin.ModelAdmin):
    pass
    fieldsets = (
        ("Basic setup", {'fields':
            ((
                'url_slug'),
                ('day_count',
                'game_count',
                'max_messages_per_day',
                'target_wins',
                'target_losses',), )}),
        ('Messaging', {'fields':
            ((
                'min_time_between_samples',
                'max_time_between_samples',
                'response_window'), )}),
        ('Payout', {'fields':
            ((
                'game_value',
                'participation_value'),
                ('bonus_value',
                'min_pct_answered_for_bonus'), )}))


class TaskDayInlineAdmin(admin.TabularInline):
    model = models.TaskDay

    readonly_fields = ('qualified_frac', )
    fields = ('task_day', 'start_time', 'end_time', 'is_game_day',
        'qualified_frac')

    extra = 0


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [TaskDayInlineAdmin]

    readonly_fields = ['status', 'total_payout_str']

    def save_model(self, request, obj, form, change):
        obj.save()
        if obj.taskday_set.count() == 0:
            obj.assign_task_days(obj.experiment.day_count)
            obj.assign_game_days(obj.random_game_day_numbers())


class IncomingTextMessageAdmin(admin.ModelAdmin):

    list_display = ('phone_number', 'created_at', '__str__')
    list_filter = ('phone_number', 'participant')

    ordering = ('-created_at', )


class OutgoingTextMessageAdmin(admin.ModelAdmin):

    list_display = ('participant', 'sent_at_precise', 'message_text')
    list_filter = ('participant', )

    ordering = ('-id', )


class ParticipantExchangeAdmin(admin.ModelAdmin):

    list_display = ('participant', 'scheduled_at', 'sent_at', 'answered_at')
    ordering = ('-scheduled_at', )
    list_filter = ('participant', )


class HiLowGameAdmin(ParticipantExchangeAdmin):

    list_display = (
        'participant', 'scheduled_at', 'sent_at', 'answered_at',
        'correct_guess', 'guessed_low', 'guess_was_correct')


class ExperienceSampleAdmin(ParticipantExchangeAdmin):

    list_display = (
        'participant', 'scheduled_at', 'sent_at', 'answered_at',
        'positive_emotion', 'negative_emotion')


class GamePermissionAdmin(ParticipantExchangeAdmin):

    list_display = (
        'participant', 'scheduled_at', 'sent_at', 'answered_at',
        'permissed')


class TaskDayAdmin(admin.ModelAdmin):

    ordering = ('task_day', )
    list_display = ('__str__', 'participant', 'task_day', 'is_game_day',
        'qualified_frac')
    list_filter = ('participant', )

admin.site.register(models.Experiment, ExperimentAdmin)
admin.site.register(models.Participant, ParticipantAdmin)
admin.site.register(models.TaskDay, TaskDayAdmin)
admin.site.register(models.IncomingTextMessage, IncomingTextMessageAdmin)
admin.site.register(models.OutgoingTextMessage, OutgoingTextMessageAdmin)
admin.site.register(models.ExperienceSample, ExperienceSampleAdmin)
admin.site.register(models.HiLowGame, HiLowGameAdmin)
admin.site.register(models.GamePermission, GamePermissionAdmin)
