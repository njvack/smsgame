from django.db import models, transaction
from django.conf import settings

import datetime
import json
import random
import re
import urllib2

from . import validators

import tropo

import logging
logger = logging.getLogger("smsgame")

SEC_IN_MIN = 60

MIN_NEEDED_TO_SCHEDULE_GAME=120
MIN_WAIT_FOR_GAME_PERMISSION=15

POST_SAMPLE_PERIOD_SEC = 90 * SEC_IN_MIN # 90 minutes
MIN_IN_POST_SAMPLE_PERIOD = 90
GAME_PERMISSION_DELTA = datetime.timedelta(
    minutes=MIN_WAIT_FOR_GAME_PERMISSION)
GAME_RUN_DELTA = datetime.timedelta(
    minutes=MIN_NEEDED_TO_SCHEDULE_GAME-MIN_WAIT_FOR_GAME_PERMISSION)
GAME_SCHEDULE_DELTA = datetime.timedelta(
    minutes=MIN_NEEDED_TO_SCHEDULE_GAME)


def is_non_string_iterable(obj):
    return hasattr(obj, '__iter__') and not hasattr(obj, 'slice')


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


class TextingTropo(tropo.Tropo):

    def say_to(self, participant, dt, message):
        if not participant.can_send_texts_at(dt):
            logger.debug("say_to: %s can't get messages more at %s" %
                (participant, dt))
            return False
        participant.outgoingtextmessage_set.create(
            sent_at=dt,
            message_text=message)
        self.say(message)
        logger.debug("Sending %s to %s" % (message, participant))
        return True

    def send_text_to(self, participant, dt, message):
        count = self.send_texts_to(participant, dt, [message])
        return count > 0

    def send_texts_to(self, participant, dt, messages):
        count = 0
        self.call(participant.phone_number.for_tropo, channel="TEXT")
        for msg in messages:
            if self.say_to(participant, dt, msg):
                count += 1
        self.hangup()
        return count


class PhoneNumberField(models.CharField):

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, PhoneNumber):
            return value

        return PhoneNumber(str(value))

    def get_prep_value(self, value):
        return PhoneNumber(str(value)).cleaned


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

    STATUSES = {
        "sleeping": {
            'time_fx': '_sleeping_contact_time', },
        "baseline": {
            'time_fx': '_baseline_contact_time',
            'status_handler': '_baseline_transition',
            'send_handler': '_baseline_send',
            'incoming_handler': '_experience_sample_incoming', },
        "game_permission": {
            'time_fx': '_game_permission_time',
            'status_handler': '_game_permission_transition',
            'send_handler': '_game_permission_send',
            'incoming_handler': '_game_permission_incoming', },
        "game_guess": {
            'time_fx': '_game_guess_time',
            'send_handler': '_game_guess_send',
            'incoming_handler': '_game_guess_incoming', },
        "game_inter_sample": {
            'time_fx': '_game_intersample_time',
            'send_handler': '_game_inter_sample_send',
            'incoming_handler': '_experience_sample_incoming', },
        "game_result": {
            'time_fx': '_game_result_time',
            'send_handler': '_game_result_send'},
        "game_post_sample": {
            'time_fx': '_game_post_sample_time',
            'send_handler': '_game_post_sample_send',
            'incoming_handler': '_experience_sample_incoming', },
        "complete": {}}

    status = models.CharField(
        max_length=20,
        default='sleeping',
        validators=[validators.IncludesValidator(STATUSES.keys())],
        editable=False)

    start_date = models.DateField()

    next_contact_time = models.DateTimeField(
        blank=True,
        null=True)

    stopped = models.BooleanField(
        default=False)

    def can_send_texts_at(self, dt):
        d1 = dt.date()
        d2 = dt+datetime.timedelta(days=1)
        text_count = self.outgoingtextmessage_set.filter(
            sent_at__range=(d1, d2)).count()
        return (
            (not self.stopped) and
            (text_count < self.experiment.max_messages_per_day))


    @transaction.commit_on_success
    def assign_pairings(self, target_external_id_list):
        if not is_non_string_iterable(target_external_id_list):
            raise TypeError("List of IDs expected")
        needed_length = (
            self.experiment.target_wins +
            self.experiment.target_losses)
        if not len(target_external_id_list) == needed_length:
            raise ValueError("List must be %s elements long" % needed_length)
        self.pairing_set.all().delete()
        for external_id in target_external_id_list:
            self.pairing_set.create(
                target=self.experiment.target_set.get(
                    external_id=external_id))

    def assign_task_days(self, num):
        self.taskday_set.all().delete()
        for i in range(num):
            tdelta = datetime.timedelta(i)
            task = self.taskday_set.create(task_day=self.start_date+tdelta)

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

    def unused_pairings(self):
        return self.pairing_set.filter(guessing_game__isnull=True)

    def random_unused_pairing(self):
        return self.unused_pairings.order_by("?")[0]

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
        gp = self.gamepermission_set.newest_if_unanswered()
        if gp and gp.scheduled_at < nct:
            nct = gp.scheduled_at
        return nct

    def _game_permission_time(self, dt):
        nct = dt
        game_permission = self.gamepermission_set.newest()
        if game_permission.sent_at:
            nct = nct+GAME_PERMISSION_DELTA
        return nct

    def _game_guess_time(self, dt):
        gg = self.guessinggame_set.newest()
        nct = dt
        if gg.sent_at is not None:
            nct = dt + datetime.timedelta(minutes=4)
        return nct

    def _game_intersample_time(self, dt):
        nct = dt+datetime.timedelta(minutes=random.randint(1, 4))
        return nct

    def _game_result_time(self, dt):
        nct = dt+datetime.timedelta(minutes=random.randint(5, 8))
        return nct

    def _game_post_sample_time(self, dt):
        # 12 += 3 minutes.
        # And it shouldn't run longer 90 minutes.
        return dt+datetime.timedelta(minutes=random.randint(9, 15))

    def generate_contact_time(self, dt):
        time_fx_name = self.STATUSES[self.status].get('time_fx')
        logger.debug("generate_contact_time fx for status %s: %s" %
            (self.status, time_fx_name))
        if time_fx_name is None:
            logger.info("Time fx name is none!")
            return
        nct = getattr(self, time_fx_name)(dt)
        logger.debug("Generated time: %s" % nct)
        return nct

    def generate_contacts_and_update_status(self, dt, skip_save=False):
        logger.debug("%s generating contacts at %s -- next_contact: %s" %
            (self, dt, self.next_contact_time))
        if self.next_contact_time is None:
            self.next_contact_time = self.generate_contact_time(dt)
        self._fire_scheduled_state_transitions(dt)
        if not skip_save:
            self.save()

    def _fire_scheduled_state_transitions(self, dt):
        # Only a few statuses get changed this way -- others result from
        # TaskDays starting/ending and responses to texts.
        status_fx_name = self.STATUSES[self.status].get('status_handler')
        if status_fx_name is None:
            logger.debug("status_handler is None")
            return
        getattr(self, status_fx_name)(dt)

    def _baseline_transition(self, dt):
        if not self.status == 'baseline':
            return
        # If there's a GamePermission coming before our next_contact_time,
        # change our next_contact time and set our status to 'game_permission'
        gp = self.gamepermission_set.newest_if_unanswered()
        if gp and dt >= gp.scheduled_at:
            self.set_status('game_permission')
        else:
            logger.debug("%s: staying baseline" % self)

    def _deny_game_permission(self, dt):
        """
        Handle the game permission -> baseline transition
        """
        logger.debug("%s: denying game permission" % (self, ))
        if not self.status == 'game_permission':
            return
        task_day = self.taskday_set.get(
            task_day=dt.date())
        gp = self.gamepermission_set.newest()
        self.set_status('baseline')
        self.next_contact_time = None
        # And delete our GamePermission
        gp.deleted_at = datetime.datetime.now()
        gp.save()
        earliest_time = dt + self.experiment.max_time_between_samples_delta
        latest_time = task_day.latest_contact - GAME_SCHEDULE_DELTA
        if (latest_time > earliest_time):
            duration = (latest_time - earliest_time).seconds
            min_sec = self.experiment.max_time_between_samples_delta.seconds
            max_sec = min_sec + duration
            sched_sec = random.randint(min_sec, max_sec)
            sched_time = dt + datetime.timedelta(seconds=sched_sec)
            gp = self.gamepermission_set.create(
                scheduled_at=sched_time)
            logger.debug("Scheduled new game permission at %s" % (
                sched_time))
        else:
            logger.debug("%s: not enough time to schedule a new game" % (self))

    def _game_permission_transition(self, dt):
        """
        Checks to see that we really have enough time to run a game,
        return to baseline if not.
        """
        if not self.status == 'game_permission':
            return
        task_day = self.taskday_set.get(
            task_day=self.next_contact_time.date())
        out_of_time = (self.next_contact_time >
            (task_day.latest_contact - GAME_SCHEDULE_DELTA))

        gp = self.gamepermission_set.newest_if_unanswered()
        permission_time_expired = False
        if gp:
            permission_time_expired = (dt >=
                (gp.scheduled_at + GAME_PERMISSION_DELTA))
        if out_of_time:
            self.set_status('baseline')
            # And delete our GamePermission
            gp.deleted_at = datetime.datetime.now()
            gp.save()
            return

        if permission_time_expired:
            self._deny_game_permission(dt)
        else:
            logger.debug("%s: staying game_permission" % self)

    def _game_post_sample_transition(self, dt):
        """
        If the highlow game was reported more than POST_SAMPLE_PERIOD_SEC
        ago, go back to baseline
        """
        if not self.status == "game_post_sample":
            return
        hlg = self.guessinggame_set.newest()
        if ((self.next_contact_time - hlg.result_reported_at).seconds <
            POST_SAMPLE_PERIOD_SEC):
            self.set_status('baseline')
        else:
            logger.debug("%s: staying game_permission" % self)

    def _baseline_send(self, dt, tropo_obj):
        es = self.experiencesample_set.create(scheduled_at=dt)
        es.mark_sent(dt)
        tropo_obj.send_text_to(
            self,
            dt,
            es.get_message_mark_sent(dt))

    def _game_permission_send(self, dt, tropo_obj):
        gp = self.gamepermission_set.newest()
        tropo_obj.send_text_to(
            self,
            dt,
            gp.get_message_mark_sent(dt))

    def _game_guess_send(self, dt, tropo_obj):
        hlg = self.guessinggame_set.newest_if_unanswered()
        foo = hlg.get_message_mark_sent(dt)
        tropo_obj.send_text_to(
            self,
            dt,
            hlg.get_message_mark_sent(dt))

    def _game_inter_sample_send(self, dt, tropo_obj):
        es = self.experiencesample_set.create(scheduled_at=dt)
        tropo_obj.send_text_to(
            self,
            dt,
            es.get_message_mark_sent(dt))
        self.set_status('game_result')

    def _game_result_send(self, dt, tropo_obj):
        hlg = self.guessinggame_set.newest()
        win_amount = self.experiment.game_value
        es = self.experiencesample_set.create(scheduled_at=dt)
        tropo_obj.send_texts_to(
            self,
            dt,
            [hlg.get_result_message_mark_sent(dt, win_amount),
            es.get_message_mark_sent(dt)])
        self.set_status('game_post_sample')

    def _game_post_sample_send(self, dt, tropo_obj):
        hlg = self.guessinggame_set.newest()
        es = self.experiencesample_set.create(scheduled_at=dt)
        tropo_obj.send_text_to(
            self,
            dt,
            es.get_message_mark_sent(dt))
        if (dt-hlg.result_reported_at).seconds >= POST_SAMPLE_PERIOD_SEC:
            logger.debug("Post-sample period over, returning to baseline")
            self.set_status('baseline')

    def _experience_sample_incoming(self, message_text, cur_time, tropo_obj):
        es = self.experiencesample_set.newest_if_unanswered()
        es.answer(message_text, cur_time)
        return es

    def _game_permission_incoming(self, message_text, cur_time, tropo_obj):
        gp = self.gamepermission_set.newest()
        gp.answer(message_text, cur_time)
        if gp.permissed:
            self.set_status('game_guess')
            game = self.guessinggame_set.create(scheduled_at=cur_time)
            tropo_obj.say_to(
                self,
                cur_time,
                game.get_message_mark_sent(cur_time))
        else:
            self._deny_game_permission(cur_time)
        return gp

    def _game_guess_incoming(self, message_text, cur_time, tropo_obj):
        hlg = self.guessinggame_set.newest_if_unanswered()
        hlg.answer(message_text, cur_time) # Raises an exception if this fails
        self.set_status('game_inter_sample')
        return hlg

    def request_tropo_contact(self, tropo_obj):
        """
        Actually makes a request for contact.
        """
        tropo_obj.request_session({
            'pk': self.pk})

    def set_status(self, new_status):
        logger.debug("%s: %s -> %s" % (self, self.status, new_status))
        self.status = new_status

    @property
    def contact_sets(self):
        return [
            self.experiencesample_set,
            self.gamepermission_set,
            self.guessinggame_set]

    def newest_contact_objects(self):
        set_objects = [s.newest() for s in self.contact_sets]
        objs = [o for o in set_objects if o]
        objs.sort(key=lambda o: o.scheduled_at)
        objs.reverse()
        return objs

    def wake_up(self, wakeup_time, skip_save=False):
        if not self.status == 'sleeping':
            return
        self.next_contact_time = self.generate_contact_time(wakeup_time)
        self.set_status('baseline')
        if not skip_save:
            self.save()

    def go_to_sleep(self, dt, complete, skip_save=False):
        self.next_contact_time = None
        if complete:
            self.set_status('complete')
        else:
            self.set_status('sleeping')
        # It's important to delete unanswered GamePermissions, so they don't
        # get used tomorrow.
        del_count = self.gamepermission_set.filter(
            answered_at=None).filter(
            deleted_at=None).update(
            deleted_at=dt)

        if not skip_save:
            self.save()

    def tropo_answer(self, incoming_msg, cur_time, tropo_obj, skip_save=False):
        # Getting a "stop" message overrides everything
        msg_text = str(incoming_msg)
        if StopMessage.is_stop_message(msg_text):
            self.stopped = True
            if not skip_save:
                self.save()
            return

        handler_fx_name = self.STATUSES[self.status].get('incoming_handler')
        logger.debug("Status: %s, incoming_handler: %s" %
            (self.status, handler_fx_name))
        if handler_fx_name is not None:
            handler_fx = getattr(self, handler_fx_name)
            try:
                handler_fx(msg_text, cur_time, tropo_obj)
            except ResponseError as e:
                logger.debug("ResponseError: %s" % e)
                tropo_obj.say_to(self, cur_time, e.message)
        if not skip_save:
            self.save()

    def tropo_send_message(self, cur_time, tropo_obj, skip_save=False):
        self.next_contact_time = None
        handler_fx_name = self.STATUSES[self.status].get('send_handler')
        logger.debug("Status: %s, send_handler: %s" %
            (self.status, handler_fx_name))

        if handler_fx_name is not None:
            handler_fx = getattr(self, handler_fx_name)
            try:
                handler_fx(cur_time, tropo_obj)
            except Exception as e:
                logger.warn("tropo_send_message went wrong: %s" % e.message)
                logger.warn("returning to baseline")
                self.set_status('baseline')
        if not skip_save:
            self.save()

    def _all_messages(self):
        lists = [s.all() for s in self.contact_sets]
        messages = [item for sublist in lists for item in sublist]
        return messages

    def message_count(self):
        return len(self._all_messages())

    def bonus_payout(self):
        return (self.experiment.bonus_value * self.task_day_count_for_bonus())

    def task_days_for_bonus(self):
        return [td for td in self.taskday_set.all()
            if td.qualifies_for_bonus()]

    def task_day_count_for_bonus(self):
        return len(self.task_days_for_bonus())

    def answered_games(self):
        return self.guessinggame_set.filter(guessed_red__isnull=False)

    def won_game_count(self):
        games = self.answered_games()
        won_games = [g for g in games if g.guess_was_correct]
        return len(won_games)

    def lost_game_count(self):
        games = self.answered_games()
        lost_games = [g for g in games if not g.guess_was_correct]
        return len(lost_games)

    def remaining_target_wins(self):
        return self.experiment.target_wins - self.won_game_count()

    def remaining_target_losses(self):
        return self.experiment.target_losses - self.lost_game_count()

    def should_win(self):
        result_array = (
            [True] * self.remaining_target_wins() +
            [False] * self.remaining_target_losses())
        return random.choice(result_array)

    def game_payout(self):
        return self.experiment.game_value*self.won_game_count()

    def total_payout(self):
        return (
            self.experiment.participation_value +
            self.game_payout() +
            self.bonus_payout())

    def total_payout_str(self):
        out_str = ''
        try:
            out_str = "$%s" % (self.total_payout())
        except:
            out_str = "Error"
        if not self.status == "complete":
            out_str += " (Not yet complete!)"
        return out_str
    total_payout_str.short_description = "Total payout"

    def __unicode__(self):
        return 'Participant %s (%s): %s' % (
            self.pk, self.status, self.phone_number)

    def save(self, *args, **kwargs):
        self.clean_fields()
        super(Participant, self).save(*args, **kwargs)


def random_slug(slug_len):
    valid_chars='bcdfghjkmnpqrstvz'

    def fx():
        vcl = len(valid_chars)
        charnums = range(slug_len)
        slug = ''.join([random.choice(valid_chars) for cn in range(slug_len)])
        return slug
    return fx


class Experiment(StampedModel):

    url_slug = models.SlugField(
        max_length=50,
        unique=True,
        default=random_slug(10))

    day_count = models.IntegerField(
        "Total task days",
        default=10)

    game_count = models.IntegerField(
        default=10)

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

    target_wins = models.IntegerField(
        default=5)

    target_losses = models.IntegerField(
        default=5)

    participation_value = models.DecimalField(
        help_text="(Dollars)",
        default=25.00,
        max_digits=5,
        decimal_places=2)

    bonus_value = models.DecimalField(
        help_text="(Dollars, per day)",
        default=4.00,
        max_digits=5,
        decimal_places=2)

    min_pct_answered_for_bonus = models.IntegerField(
        "Bonus percent",
        help_text="Minimum percent of texts answered for bonus",
        default=90)

    def __unicode__(self):
        return "Experiment %s: %s days, %s games" % (
            self.pk, self.day_count, self.game_count)

    @property
    def min_time_between_samples_delta(self):
        return datetime.timedelta(minutes=self.min_time_between_samples)

    @property
    def max_time_between_samples_delta(self):
        return datetime.timedelta(minutes=self.max_time_between_samples)


class ResponseError(ValueError):
    pass


class Target(StampedModel):

    experiment = models.ForeignKey("Experiment")

    external_id = models.CharField(max_length=100)

    message = models.CharField(max_length=140)

    class Meta:

        unique_together = ('experiment', 'external_id')


class Pairing(StampedModel):

    target = models.ForeignKey("Target")

    participant = models.ForeignKey("Participant")

    guessing_game = models.ForeignKey("GuessingGame",
        blank=True,
        null=True)


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


class ParticipantExchange(StampedModel):

    objects = ParticipantExchangeManager()

    participant = models.ForeignKey(
        "Participant")

    incoming_text = models.ForeignKey(
        "IncomingTextMessage",
        null=True,
        blank=True,
        editable=False)

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True)

    sent_at = models.DateTimeField(
        null=True,
        blank=True)

    answered_at = models.DateTimeField(
        null=True,
        blank=True)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True)

    participant_status_when_sent = models.CharField(
        max_length=20,
        null=True,
        blank=True)

    def mark_sent(self, recorded_time, skip_save=False):
        self.sent_at = recorded_time
        self.participant_status_when_sent = self.participant.status
        if not skip_save:
            self.save()

    def was_answered_within(self, seconds):
        if self.answered_at is None:
            return False
        delta_sec = (self.answered_at - self.sent_at).seconds
        return (delta_sec <= seconds)

    def was_answered_within_window(self):
        return self.was_answered_within(
            self.participant.experiment.response_window)

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
            matches = parse_re.match(text)
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

    def get_message_mark_sent(self, dt, skip_save=False):
        self.mark_sent(dt, True)
        if not skip_save:
            self.save()
        return "Enter how much positive emotion (1-9) and negative emotion (1-9) you are feeling right now."


class GamePermission(ParticipantExchange):

    permissed = models.BooleanField(
        default=False)

    def get_message_mark_sent(self, dt, skip_save=False):
        self.mark_sent(dt, True)
        if not skip_save:
            self.save()
        return "Are you ready to play a game and answer more text messages for the next two hours? (y/n)"

    def answer(self, text, answered_at, skip_save=False):
        """
        Allow any text that has a Y or N in it.
        """
        matches = re.match(
            r"""
            [^yn]*
            (?P<permission_char>[yn])
            [^yn]*
            """, text, (re.I | re.VERBOSE))
        try:
            match = matches.group("permission_char").lower()
            self.permissed = (match == "y")
        except:
            raise ResponseError("We didn't understand your repsonse. Please enter y or n.")

        self.answered_at = answered_at
        if not skip_save:
            self.save()


class GuessingGame(ParticipantExchange):

    red_correct = models.NullBooleanField(
        blank=True,
        null=True)

    guessed_red = models.NullBooleanField(
        blank=True,
        null=True)

    result_reported_at = models.DateTimeField(
        blank=True,
        null=True)

    def answer(self, text, answered_at, skip_save=False):
        """
        Allow any text that has 'r' or 'b'
        """
        matches = re.match(
            r"""
            [^rb]*
            (?P<guess_char>[rb])
            [^rb]*
            """, text, (re.I | re.VERBOSE))
        try:
            match = matches.group("guess_char").lower()
            self.guessed_red = (match == "r")
        except:
            raise ResponseError("We didn't understand your repsonse. Please enter red or black.")

        if self.participant.should_win():
            self.red_correct = self.guessed_red
        else:
            self.red_correct = not self.guessed_red

        self.answered_at = answered_at
        if not skip_save:
            self.save()

    def get_message_mark_sent(self, dt, skip_save=False):
        self.mark_sent(dt, True)
        if not skip_save:
            self.save()
        return "A random card is being selected from a full deck of cards. Guess whether the card will be red or black."

    @property
    def guess_was_correct(self):
        return (self.red_correct == self.guessed_red)

    def get_result_message_mark_sent(self, dt, win_dollars, skip_save=False):
        if self.guess_was_correct:
            msg = "You won $20 for %(message)s" % {'message': '<MESSAGE>'}
        else:
            msg = "You didn't win for %(message)s" % {'message': '<MESSAGE>'}
        self.result_reported_at = dt
        if not skip_save:
            self.save()
        return msg


STOP_RE = re.compile(
    r"""
    (STOP|END|CANCEL|UNSUBSCRIBE|QUIT|STOP ALL)
    """, (re.I | re.VERBOSE))


class StopMessage(object):

    @classmethod
    def is_stop_message(klass, msg):
        return STOP_RE.match(msg)


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
            game_time = self.random_time_before_day_end(
                GAME_SCHEDULE_DELTA)
            self.participant.gamepermission_set.create(
                scheduled_at=game_time)
        self.participant.wake_up(dt, skip_save)

    def end_day(self, dt, skip_save=False):
        self.set_status_for_time(dt, skip_save)
        complete = self.is_last_task_day()
        self.participant.go_to_sleep(dt, complete, skip_save)

    def random_time_before_day_end(self, delta):
        day_len = (self.latest_contact - self.earliest_contact)
        available_time_sec = day_len.seconds - delta.seconds
        offset_sec = random.randint(0, available_time_sec)
        dt = self.earliest_contact + datetime.timedelta(seconds=offset_sec)
        return dt

    def is_last_task_day(self):
        last_task_day = self.participant.taskday_set.latest('task_day')
        return self == last_task_day

    def _all_messages(self):
        sets = [
            self.experiencesample_set,
            self.gamepermission_set,
            self.guessinggame_set]
        lists = [s.all() for s in sets]
        return [item for sublist in lists for item in sublist]

    def message_count(self):
        return len(self._all_messages())

    def messages_for_bonus(self):
        msgs = self._all_messages()
        bonus_messages = [m for m in msgs if m.was_answered_within(
            self.participant.experiment.response_window)]
        return bonus_messages

    def message_count_for_bonus(self):
        return len(self.messages_for_bonus())

    def qualified_frac(self):
        if (self.message_count() == 0):
            return 0
        return 100*float(self.message_count_for_bonus())/self.message_count()

    def qualifies_for_bonus(self):
        return (self.qualified_frac() >=
            self.participant.experiment.min_pct_answered_for_bonus)

    def _participantexchange_set(self, specific_set):
        d2 = self.task_day + datetime.timedelta(days=1)
        return specific_set.filter(sent_at__range=(self.task_day, d2))

    @property
    def experiencesample_set(self):
        return self._participantexchange_set(
            self.participant.experiencesample_set)

    @property
    def gamepermission_set(self):
        return self._participantexchange_set(
            self.participant.gamepermission_set)

    @property
    def guessinggame_set(self):
        return self._participantexchange_set(
            self.participant.guessinggame_set)

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
        Participant)

    message_text = models.CharField(
        max_length=160)

    sent_at = models.DateTimeField()

    def sent_at_precise(self):
        return self.sent_at.strftime("%Y-%m-%d %H:%M:%S")
    sent_at_precise.short_description = "Sent at"


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
