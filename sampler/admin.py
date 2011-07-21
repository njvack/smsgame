from django.contrib import admin
from . import models


class TaskDayInlineAdmin(admin.TabularInline):
    model = models.TaskDay

    fields = ('task_day', 'start_time', 'end_time')

    extra = 0


class ParticipantAdmin(admin.ModelAdmin):
    inlines = [TaskDayInlineAdmin]

    def save_model(self, request, obj, form, change):
        obj.save()
        if obj.taskday_set.count() == 0:
            obj.assign_task_days(obj.experiment.day_count)
            obj.assign_game_days(obj.random_game_day_numbers())


admin.site.register(models.Experiment)
admin.site.register(models.Participant, ParticipantAdmin)
admin.site.register(models.TaskDay)
