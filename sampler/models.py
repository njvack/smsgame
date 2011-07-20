from django.db import models
from django.conf import settings

import datetime


class StampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Participant(StampedModel):

    experiment = models.ForeignKey("Experiment")

    phone_number = models.CharField(
        max_length=255,
        unique=True)

    PPT_STATUSES = (
        ("waiting", "Waiting to run"),
        ("baseline", "Baseline"),
        ("game", "Game on!"),
        ("done", "All done!"))

    status = models.CharField(
        max_length=20,
        choices=PPT_STATUSES,
        default=PPT_STATUSES[0])

    start_date = models.DateField()

    next_contact_time = models.DateTimeField(
        blank=True,
        null=True,
        editable=False)

    def save(self, *args, **kwargs):
        super(Participant, self).save(*args, **kwargs)
        if self.taskday_set.count() == 0:
            for daynum in range(self.experiment.day_count):
                tdelta = datetime.timedelta(daynum)
                task = TaskDay(
                    participant=self,
                    task_day=self.start_date+tdelta)
                task.save()

    def __unicode__(self):
        return "Participant %s (%s), starts %s" % (
            self.pk, self.phone_number, self.start_date)

        
class Experiment(StampedModel):
    
    EXPERIMENT_STATUSES = (
        ("active", "Active"),
        ("inactive", "Inactive"))

    status = models.CharField(
        max_length=20,
        choices=EXPERIMENT_STATUSES,
        default=EXPERIMENT_STATUSES[0])

    day_count = models.IntegerField(
        default=7)

    game_count = models.IntegerField(
        default=5)
    
    objects = models.Manager()
    
    def __unicode__(self):
        return "Experiment %s (%s): %s days, %s games" % (
            self.pk, self.status, self.day_count, self.game_count)


class TaskDay(StampedModel):

    participant = models.ForeignKey("Participant")

    task_day = models.DateField()

    start_time = models.TimeField(
        default="8:00")

    end_time = models.TimeField(
        default="22:00")

    is_game_day = models.BooleanField(
        "Play game this day",
        default=False)
    
    def __unicode__(self):
        return "%s (%s-%s)" % (
            self.task_day, self.start_time, self.end_time)
