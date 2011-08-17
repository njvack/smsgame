from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse


import datetime
import json
import random
import re
import urllib2

from . import validators

import logging
logger = logging.getLogger("smsgame")

SEC_IN_MIN = 60
GAME_PADDING_SEC = 150 * SEC_IN_MIN
POST_SAMPLE_PERIOD_SEC = 120 * SEC_IN_MIN


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

    STATUSES = (
        "sleeping",
        "baseline",
        "game_permission",
        "game_guess",
        "game_inter_sample",
        "game_result",
        "game_post_sample",
        "complete")

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

    def get_or_create_contact(self):
        obj = None
        if (
            self.status == 'baseline' or
            self.status == 'game_inter_sample' or
            self.status == 'game_post_sample'):

            obj = self.experiencesample_set.schedule_at(self.next_contact_time)
        elif (self.status == 'game_permission'):
            obj = self.gamepermission_set.schedule_at(self.next_contact_time)
        elif (self.status == 'game_guess'):
            obj = self.hilowgame_set.schedule_at(self.next_contact_time)
        elif (self.status == 'game_result'):
            obj = self.hilowgame_set.newest()

        return obj

    def _sleeping_contact_time(self, dt):
        delta = datetime.timedelta(minutes=random.randint(
            0, self.experiment.min_time_between_samples))
        nct = dt+delta
        return nct

    def _baseline_contact_time(self, dt):
        delta = datetime.timedelta(minutes=random.randint(
            self.experiment.min_time_between_samples,
            self.experiment.max_time_between_samples))
        nct = dt+delta
        return nct

    def _game_permission_time(self, dt):
        game_permission = self.gamepermission_set.newest_if_unanswered()
        nct = dt
        if game_permission.sent_at:
            nct = nct+datetime.timedelta(minutes=15)
        return nct

    def _game_intersample_time(self, dt):
        nct = dt+datetime.timedelta(minutes=random.randint(1, 4))
        return nct

    def _game_result_time(self, dt):
        nct = dt+datetime.timedelta(minutes=random.randint(5, 8))
        return nct

    def _game_post_sample_time(self, dt):
        # Immediate if it's the first sample
        # 12 += 3 if it's in the first hour
        # 23 += 5 if it's in the second hour
        # And it shouldn't run longer than that.
        nct = dt
        game = self.hilowgame_set.newest()
        # Not having a game is impossible, should be an error -- let it.
        rep_delta = (dt-game.result_reported_at).seconds
        samples = self.experiencesample_set.filter(
            scheduled_at__gt=game.result_reported_at)
        if samples.count() == 0:
            pass
        elif rep_delta < 60*SEC_IN_MIN:
            nct = dt+datetime.timedelta(minutes=random.randint(9, 15))
        else:
            nct = dt+datetime.timedelta(minutes=random.randint(18, 28))
        return nct

    def generate_contact_time(self, dt):

        nct = None
        if self.status == "sleeping":
            nct = self._sleeping_contact_time(dt)
        elif self.status == "baseline":
            nct = self._baseline_contact_time(dt)
        elif self.status == "game_permission":
            nct = self._game_permission_time(dt)
        elif self.status == "game_guess":
            nct = dt
        elif self.status == "game_inter_sample":
            nct = self._game_intersample_time(dt)
        elif self.status == "game_result":
            nct = self._game_result_time(dt)
        elif self.status == "game_post_sample":
            nct = self._game_post_sample_time(dt)
        return nct

    def generate_contacts_and_update_status(self, dt):
        logger.debug("%s generating contacts at %s -- next_contact: %s" %
            (self, dt, self.next_contact_time))
        if self.next_contact_time is not None:
            return
        self.next_contact_time = self.generate_contact_time(dt)
        self.fire_scheduled_state_transitions()
        return self.get_or_create_contact()

    def fire_scheduled_state_transitions(self, skip_save=False):
        # Only a few statuses get changed this way -- others result from
        # TaskDays starting/ending and responses to texts.
        if self.status == "baseline":
            self._baseline_transition()
        elif self.status == "game_permission":
            self._game_permission_transition()
        elif self.status == "game_post_sample":
            self._game_post_sample_transition()
        if not skip_save:
            self.save()

    def _baseline_transition(self):
        if not self.status == 'baseline':
            return
        # If there's a GamePermission coming before our next_contact_time,
        # change our next_contact time and set our status to 'game_permission'
        gp = self.gamepermission_set.newest_if_unanswered()
        if gp and self.next_contact_time > gp.scheduled_at:
            logger.debug("%s: baseline -> game_permission" % self)
            self.status = "game_permission"
            self.next_contact_time = gp.scheduled_at
            # There will also be an ExperienceSample wating out there --
            # kill it
            self.experiencesample_set.filter(
                scheduled_at__gte=self.next_contact_time).filter(
                answered_at=None).update(deleted_at=datetime.datetime.now())
        else:
            logger.debug("%s: staying baseline" % self)

    def _game_permission_transition(self):
        """
        Checks to see that we really have enough time to run a game,
        return to baseline if not.
        """
        if not self.status == "game_permission":
            return
        task_day = self.taskday_set.get(
            task_day=self.next_contact_time.date())
        if ((task_day.latest_contact - self.next_contact_time).seconds <
            GAME_PADDING_SEC):
            logger.debug("%s: game_permission -> baseline" % self)
            self.status = "baseline"
            # And delete our GamePermission
            gps = self.gamepermission_set.newest_unanswered()
            gps.deleted_at = datetime.datetime.now()
            gps.save()
        else:
            logger.debug("%s: staying game_permission" % self)

    def _game_post_sample_transition(self):
        """
        If the highlow game was reported more than POST_SAMPLE_PERIOD_SEC
        ago, go back to baseline
        """
        if not self.status == "game_post_sample":
            return
        hlg = self.hilowgame_set.newest()
        if ((self.next_contact_time - hlg.result_reported_at).seconds <
            POST_SAMPLE_PERIOD_SEC):
            logger.debug("%s: game_permission -> baseline" % self)
            self.status = "baseline"
        else:
            logger.debug("%s: staying game_permission" % self)

    def make_contact(self, recorded_time, tropo_requester, skip_save=False):
        """
        Actually makes a request for contact. Sets the current contact object
        as marked sent, clears self.next_contact_time.
        """
        tropo_requester.request_session({
            'pk': self.pk})

        obj = self.current_contact_object()
        obj.mark_sent(recorded_time, skip_save)
        self.next_contact_time = None
        if not skip_save:
            self.save()

    @property
    def contact_sets(self):
        return [
            self.experiencesample_set,
            self.gamepermission_set,
            self.hilowgame_set]

    def newest_contact_objects(self):
        set_objects = [s.newest() for s in self.contact_sets]
        objs = [o for o in set_objects if o]
        objs.sort(key=lambda o: o.scheduled_at)
        objs.reverse()
        return objs

    def current_contact_object(self):
        ncos = self.newest_contact_objects()
        fco = None
        if len(ncos) > 0:
            fco = ncos[0]
            if fco.answered_at is not None:
                fco = None
        return fco

    def wake_up(self, wakeup_time, skip_save=False):
        if not self.status == 'sleeping':
            return
        logger.debug("%s: sleeping -> baseline" % self)
        self.next_contact_time = self.generate_contact_time(wakeup_time)
        self.status = 'baseline'
        if not skip_save:
            self.save()
        self.get_or_create_contact()

    def get_game_guess(self):
        pass

    def game_intersample(self):
        pass

    def game_reveal(self):
        pass

    def game_post_sample(self):
        pass

    def return_to_baseline(self):
        pass

    def go_to_sleep(self, complete, skip_save=False):
        prev_status = self.status
        self.next_contact_time = None
        if complete:
            self.status = 'complete'
        else:
            self.status = 'sleeping'
        logger.debug("%s: %s -> %s" % (self, prev_status, self.status))
        if not skip_save:
            self.save()

    def tropo_answer(self, incoming_msg, cur_time, tropo_req):
        obj = self.current_contact_object()
        logger.debug("Current object: %s" % obj)
        try:
            obj.answer(incoming_msg, cur_time)
        except ResponseError as e:
            logger.debug("ResponseError: %s" % e)
            tropo_req.say(e.message)
        except Exception as e:
            logger.debug(e)
            tropo_req.hangup()

    def __unicode__(self):
        return 'Participant %s (%s): %s' % (
            self.pk, self.status, self.phone_number)

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


class ResponseError(ValueError):
    pass


class ParticipantExchangeManager(models.Manager):

    def active(self):
        return self.get_query_set().filter(deleted_at=None)

    def newest_if_unanswered(self):
        pe = self.newest()
        if pe and pe.answered_at is None:
            return pe
        return None

    def newest(self):
        try:
            return self.active().latest('created_at')
        except:
            return None

    def schedule_at(self, dt):
        cur_obj = self.newest_if_unanswered()
        if cur_obj is not None:
            cur_obj.scheduled_at = dt
            cur_obj.save()
        else:
            cur_obj = self.create(scheduled_at=dt)
        return cur_obj


class ParticipantExchange(StampedModel):

    objects = ParticipantExchangeManager()

    participant = models.ForeignKey(
        "Participant",
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

    deleted_at = models.DateTimeField(
        null=True,
        blank=True)

    def mark_sent(self, recorded_time, skip_save=False):
        self.sent_at = recorded_time
        if not skip_save:
            self.save()

    class Meta:
        abstract = True
        ordering = ['-scheduled_at']


class ExperienceSample(ParticipantExchange):

    positive_emotion = models.IntegerField(
        null=True,
        blank=True)

    negative_emotion = models.IntegerField(
        null=True,
        blank=True)

    def answer(self, text, answered_at, skip_save=False):
        """
        Tries to parse a response (throws an exception if it fails),
        and if it succeeds, set the answered time, positive_emotion,
        negative_emotion, and yeah.
        """
        parse_re = re.compile(
                r"""
                ^[^1-9]*
                (?P<positive_emotion>[1-9])
                [^1-9]*
                (?P<negative_emotion>[1-9])
                [^1-9]*$""",
            re.VERBOSE)

        try:
            matches = parse_re.match(str(text))
            self.positive_emotion = matches.group('positive_emotion')
            self.negative_emotion = matches.group('negative_emotion')
        except Exception as exc:
            raise ResponseError("We didn't understand your response. Please enter two numbers between 1 and 9.")

        self.answered_at = answered_at
        if not skip_save:
            self.save()

    @property
    def val_tuple(self):
        return (self.positive_emotion, self.negative_emotion)

    def __str__(self):
        return "%s %s" % (self.positive_emotion, self.negative_emotion)

    def message(self):
        return "Enter how much positive emotion (1-9) and negative emotion (1-9) you are feeling right now."


class GamePermission(ParticipantExchange):

    permissed = models.BooleanField(
        default=False)

    def message(self):
        return "Are you ready to play a game and answer more text messages for the next two hours? (y/n)"


def random_hi_low():
    num = random.randint(1, 8)
    if num >= 5:
        num += 1
    return num


class HiLowGame(ParticipantExchange):

    correct_guess = models.IntegerField(
        default=random_hi_low)

    guessed_low = models.NullBooleanField(
        blank=True,
        null=True)

    result_reported_at = models.DateTimeField(
        blank=True,
        null=True)

    def message(self):
        return "We generated a number between 1 and 9. Guess if it's lower or higher than 5. (low/high)"

    def result_message(self):
        is_low = self.correct_guess < 5
        if (is_low == guessed_low):
            msg = "The number was %s. You guessed right! $20 has been added to your account." % self.correct_guess
        else:
            msg = "The number was %s. You guessed wrong. No money additional money has been added to your account."
        return msg


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
        if self.is_game_day:
            game_time = self.random_time_before_day_end(GAME_PADDING_SEC)
            self.participant.gamepermission_set.create(
                scheduled_at=game_time)
        self.participant.wake_up(dt, skip_save)

    def end_day(self, td, skip_save=False):
        self.set_status_for_time(td, skip_save)
        complete = self.is_last_task_day
        self.participant.go_to_sleep(complete, skip_save)

    def random_time_before_day_end(self, before_end_sec):
        day_len = (self.latest_contact - self.earliest_contact)
        available_time_sec = day_len.seconds - before_end_sec
        offset_sec = random.randint(0, available_time_sec)
        dt = self.earliest_contact + datetime.timedelta(seconds=offset_sec)
        return dt

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

    def __str__(self):
        return str(self.message_text)


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
        logger.debug("Requesting session with opts: %s" % my_opts)
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
