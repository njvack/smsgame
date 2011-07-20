from django.contrib import admin
from . import models

class TaskDayInlineAdmin(admin.TabularInline):
    model = models.TaskDay
    
    fields = ('task_day', 'start_time', 'end_time')
    
    extra = 0

class ParticipantAdmin(admin.ModelAdmin):
    inlines = [
        TaskDayInlineAdmin
    ]

admin.site.register(models.Experiment)
admin.site.register(models.Participant, ParticipantAdmin)
admin.site.register(models.TaskDay)