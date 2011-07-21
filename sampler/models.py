from django.db import models
from django.conf import settings

import datetime
import random


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

    def assign_task_days(self, num):
        for i in range(num):
            tdelta = datetime.timedelta(i)
            task = TaskDay(
                participant=self,
                task_day=self.start_date+tdelta)
            task.save()

    def assign_game_days(self, day_numbers):
        # First, clear the existing days...
        self.taskday_set.update(is_game_day=False)
        task_days = self.taskday_set.all()
        for dnum in day_numbers:
            task_day = task_days[dnum]
            task_day.is_game_day = True
            task_day.save()

    def random_game_day_numbers(self):
        return random.sample(
            range(self.experiment.day_count),
            self.experiment.game_count)

    def save(self, *args, **kwargs):
        super(Participant, self).save(*args, **kwargs)
        if self.taskday_set.count() == 0:
            self.assign_task_days(self.experiment.day_count)
            self.assign_game_days(self.random_game_day_numbers())

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


class IncomingTextMessage(StampedModel):

    participant = models.ForeignKey(Participant, blank=True, null=True)

    phone_number = models.CharField(
        max_length=255)

    message_text = models.CharField(
        max_length=255)

    tropo_json = models.TextField()


class OutgoingTextMessage(StampedModel):

    participant = models.ForeignKey(Participant, blank=True, null=True)

    phone_number = models.CharField(
        max_length=255)

    message_text = models.CharField(
        max_length=140)

    tropo_json = models.TextField()
