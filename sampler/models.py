from django.db import models
from django.conf import settings

import datetime
import json
import random
import re
import urllib2

from . import validators

import logging
logger = logging.getLogger("smsgame")


class PhoneNumber(object):

    description = "A 10-digit US telephone number"

    def __init__(self, number_string):
        self.original_string = number_string
        ns = re.sub("\D", "", number_string)
        ns = re.sub("^1", "", ns)
        self.cleaned = ns

    def __unicode__(self):
        n = self.cleaned
        if len(n) == 7:
            return self.seven_digit
        if len(n) == 10:
            return self.ten_digit
        return n

    @property
    def seven_digit(self):
        n = self.cleaned
        return "%s-%s" % (n[0:3], n[3:])

    @property
    def ten_digit(self):
        n = self.cleaned
        return "(%s) %s-%s" % (n[0:3], n[3:6], n[6:])

    @property
    def for_tropo(self):
        """ Return something like 16085551212 """
        return "1%s" % self.cleaned

    def __len__(self):
        return len(self.cleaned)

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        sstr = str(self)
        ostr = str(other)
        return (sstr == ostr) and (len(sstr) > 0) and other is not None
        return str(self) == str(other)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "%s.%s('%s')" % (
            self.__class__.__module__,
            self.__class__.__name__,
            str(self))


class PhoneNumberField(models.CharField):

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, PhoneNumber):
            return value

        return PhoneNumber(str(value))

    def get_prep_value(self, value):
        return value.cleaned

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^sampler\.models\.PhoneNumberField"])


class StampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Participant(StampedModel):

    experiment = models.ForeignKey('Experiment')

    phone_number = PhoneNumberField(
        max_length=255,
        unique=True)

    STATUSES = ('baseline', 'game', 'complete')

    status = models.CharField(
        max_length=20,
        default=STATUSES[0],
        validators=[validators.IncludesValidator(STATUSES)])

    start_date = models.DateField()

    next_contact_time = models.DateTimeField(
        blank=True,
        null=True)

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
    
    def generate_contact_after(self, dt, skip_save=False):
        minutes = random.randint(
            self.experiment.min_time_between_samples,
            self.experiment.max_time_between_samples)
        delta = datetime.timedelta(minutes=minutes)
        self.next_contact_time = dt+delta
        sample = self.experiencesample_set.create(
            scheduled_at=self.next_contact_time)
        if not skip_save:
            self.save()
    
    def current_contact_type(self):
        """ Returns something like 'experiencesample'  or 'game_confirmation' 
        Always 'expreiencesample' or None now
        """
        es = self.experiencesample_set.order_by("-scheduled_at")[0]
        if es.answered_at is None:
            return 'experiencesample'
        return None
    
    def wake_up(self, first_contact_time, skip_save=False):
        self.status = 'baseline'
        self.next_contact_time = first_contact_time
        if not skip_save:
            self.save()
    
    def go_to_sleep(self, complete, skip_save=False):
        self.next_contact_time = None
        if complete:
            self.status = 'complete'
        if not skip_save:
            self.save()

    def __unicode__(self):
        return 'Participant %s: %s, starts %s' % (
            self.pk, self.phone_number, self.start_date)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super(Participant, self).save(*args, **kwargs)


class Experiment(StampedModel):

    day_count = models.IntegerField(
        "Total task days",
        default=7)

    game_count = models.IntegerField(
        default=5)

    max_messages_per_day = models.IntegerField(
        default=35)

    min_time_between_samples = models.IntegerField(
        help_text="(Minutes)",
        default=60)

    max_time_between_samples = models.IntegerField(
        help_text="(Minutes)",
        default=90)

    response_window = models.IntegerField(
        help_text="(Seconds)",
        default=420) # 7 minutes

    game_value = models.DecimalField(
        help_text="(Dollars)",
        default=20.00,
        max_digits=5,
        decimal_places=2)

    participation_value = models.DecimalField(
        help_text="(Dollars)",
        default=25.00,
        max_digits=5,
        decimal_places=2)

    bonus_value = models.DecimalField(
        help_text="(Dollars)",
        default=40.00,
        max_digits=5,
        decimal_places=2)

    min_pct_answered_for_bonus = models.IntegerField(
        "Bonus percent",
        help_text="Minimum percent of texts answered for bonus",
        default=90)

    def __unicode__(self):
        return "Experiment %s: %s days, %s games" % (
            self.pk, self.day_count, self.game_count)


class ExperienceSample(StampedModel):

    participant = models.ForeignKey(
        "Participant",
        editable=False)

    outgoing_text = models.ForeignKey(
        "OutgoingTextMessage",
        null=True,
        blank=True,
        editable=False)

    incoming_text = models.ForeignKey(
        "IncomingTextMessage",
        null=True,
        blank=True,
        editable=False)

    scheduled_at = models.DateTimeField()

    sent_at = models.DateTimeField(
        null=True,
        blank=True)

    answered_at = models.DateTimeField(
        null=True,
        blank=True)

    positive_emotion = models.IntegerField(
        null=True,
        blank=True)

    negative_emotion = models.IntegerField(
        null=True,
        blank=True)


class TaskDayWaitingManager(models.Manager):

    def get_query_set(self):
        return super(TaskDayWaitingManager, self).get_query_set().filter(
            status='waiting')

    def for_datetime(self, dt):
        return self.get_query_set().filter(
            earliest_contact__lte=dt).filter(
            latest_contact__gte=dt)


class TaskDayActiveManager(models.Manager):

    def get_query_set(self):
        return super(TaskDayActiveManager, self).get_query_set().filter(
            status='active')

    def for_datetime(self, dt):
        return self.get_query_set().filter(
            earliest_contact__lte=dt).filter(
            latest_contact__gte=dt)

    def expiring(self, dt):
        return self.get_query_set().filter(
            latest_contact__lte=dt)


class TaskDay(StampedModel):

    objects = models.Manager()

    waiting = TaskDayWaitingManager()

    active = TaskDayActiveManager()

    STATUSES = ('waiting', 'active', 'complete')

    status = models.CharField(
        max_length=255,
        default=STATUSES[0],
        validators=[validators.IncludesValidator(STATUSES)])

    participant = models.ForeignKey("Participant")

    task_day = models.DateField()

    start_time = models.TimeField(
        default=datetime.time(8, 00))

    end_time = models.TimeField(
        default=datetime.time(22, 00))

    earliest_contact = models.DateTimeField(
        editable=False)

    latest_contact = models.DateTimeField(
        editable=False)

    is_game_day = models.BooleanField(
        "Play game this day",
        default=False)

    def __unicode__(self):
        return "TaskDay %s: %s (%s-%s)" % (
            self.pk, self.task_day, self.start_time, self.end_time)

    def set_status_for_time(self, dt, skip_save=False):
        self.__set_contact_fields()
        if dt < self.earliest_contact:
            self.status = 'waiting'
        elif dt >= self.earliest_contact and dt < self.latest_contact:
            self.status = 'active'
        else:
            self.status = 'complete'

        if not skip_save:
            self.save()

    def start_day(self, dt, skip_save=False):
        """
        Set my status to active, and schedule a first contact for my ppt
        """
        self.set_status_for_time(dt, skip_save)
        self.participant.wake_up(
            self.get_random_first_contact_time(),
            skip_save)
    
    def end_day(self, td, skip_save=False):
        self.set_status_for_time(td, skip_save)
        complete = self.is_last_task_day
        self.participant.go_to_sleep(complete, skip_save)

    def get_random_first_contact_time(self):
        tdelta = datetime.timedelta(
            minutes=random.randint(0,
                self.participant.experiment.min_time_between_samples))
        return self.earliest_contact + tdelta
        
    def is_last_task_day(self):
        last_task_day = self.participant.taskday_set.latest('task_day')
        return self == last_task_day

    def __set_contact_fields(self):
        self.earliest_contact = datetime.datetime(
            self.task_day.year, self.task_day.month, self.task_day.day,
            self.start_time.hour, self.start_time.minute)

        self.latest_contact = datetime.datetime(
            self.task_day.year, self.task_day.month, self.task_day.day,
            self.end_time.hour, self.end_time.minute)

    def save(self, *args, **kwargs):
        self.clean_fields()
        self.__set_contact_fields()
        super(TaskDay, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('participant', 'task_day')


class IncomingTextMessage(StampedModel):

    participant = models.ForeignKey(
        Participant,
        blank=True,
        null=True)

    phone_number = PhoneNumberField(
        max_length=255)

    message_text = models.CharField(
        max_length=160)

    tropo_json = models.TextField()


class OutgoingTextMessage(StampedModel):

    participant = models.ForeignKey(
        Participant,
        blank=True,
        null=True)

    phone_number = PhoneNumberField(
        max_length=255)

    message_text = models.CharField(
        max_length=160)

    tropo_json = models.TextField()


class OutgoingTropoSession(object):

    def __init__(
        self,
        url=settings.TROPO_SESSION_URL,
        sms_token=settings.TROPO_SMS_TOKEN):

        self.url = url
        self.sms_token = sms_token

    def request_session(self, options):
        my_opts = {}
        my_opts.update(dict(options))
        my_opts.update({'token': self.sms_token})
        for k, v in my_opts.iteritems():
            my_opts[k] = str(v)
        opts_json = json.dumps(dict(my_opts))
        req = urllib2.Request(self.url,
            opts_json, {'content-type': 'application/json'})
        stream = urllib2.urlopen(req)
        response = stream.read()
        stream.close()
        resp_dict = json.loads(response)
        if 'id' in resp_dict:
            resp_dict['id'] = resp_dict['id'].strip()

        return resp_dict
