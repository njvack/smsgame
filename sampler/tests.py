from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings

import random
import datetime

from . import models
from . import mocks
from . import validators
from . import views
from sampler.management.commands import schedule_and_send_messages


class ParticipantTest(TestCase):

    def setUp(self):
        random.seed(0)
        self.today = datetime.date(2011, 7, 1) # Not really today.
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today,
            phone_number='6085551212')
        self.early = datetime.datetime(2011, 7, 1, 8, 30)
        self.td_start = datetime.datetime(2011, 7, 1, 9, 30)
        self.td_end = datetime.datetime(2011, 7, 1, 19, 00)
        self.late = datetime.datetime(2011, 7, 1, 20, 00)
        self.td1 = self.p1.taskday_set.create(
            task_day=self.td_start.date(),
            start_time=self.td_start.time(),
            end_time=self.td_end.time())

    def testPptDoesntAllowCrazyStatus(self):
        p1 = self.p1
        p1.status = "crazy"
        with self.assertRaises(ValidationError):
            p1.save()

    def testGenOrUpdateStatusBaseline(self):
        self.p1.status = 'baseline'
        self.p1.next_contact_time = self.td_start
        self.p1.gamepermission_set.create(scheduled_at=self.td_start)
        self.p1.generate_contacts_and_update_status(self.td_start)
        self.assertEqual("game_permission", self.p1.status)

    def testBaselineToPermissionTransition(self):
        self.p1.status = 'baseline'
        self.p1.next_contact_time = self.td_start
        self.p1.gamepermission_set.create(scheduled_at=self.td_start)
        self.p1._fire_scheduled_state_transitions()
        self.assertEqual("game_permission", self.p1.status)

    def testSendIntersampleMakesExpSample(self):
        t = mocks.Tropo()
        self.p1.status = 'game_inter_sample'
        self.p1.next_contact_time = self.td_start
        self.p1.tropo_send_message(self.td_start, t, True)
        self.assertEqual(1, self.p1.experiencesample_set.count())
        self.assertEqual(1, t.things_said)

    def testSendPostSampleMakesExpSample(self):
        t = mocks.Tropo()
        self.p1.status = 'game_post_sample'
        self.p1.next_contact_time = self.td_start
        self.p1.tropo_send_message(self.td_start, t, True)
        self.assertEqual(1, self.p1.experiencesample_set.count())
        self.assertEqual(1, t.things_said)

    def testNewestContactObjects(self):
        p = self.p1
        t = self.early
        t2 = self.late
        self.assertEqual(0, len(p.newest_contact_objects()))
        p.experiencesample_set.create(scheduled_at=t)
        self.assertEqual(1, len(p.newest_contact_objects()))
        p.experiencesample_set.create(scheduled_at=t2)
        self.assertEqual(1, len(p.newest_contact_objects()))
        p.gamepermission_set.create(scheduled_at=t)
        self.assertEqual(2, len(p.newest_contact_objects()))
        p.hilowgame_set.create(scheduled_at=t)
        self.assertEqual(3, len(p.newest_contact_objects()))

    def testBaselineTransition(self):
        p = self.p1
        p.status = 'baseline'
        p.gamepermission_set.create(scheduled_at=self.early)
        p.next_contact_time = self.td_start
        p.save()
        p._baseline_transition()
        self.assertEqual(p.status, 'game_permission')

    def testAnswerWithExpSampleAndGame(self):
        p = self.p1
        t = mocks.Tropo()
        p.gamepermission_set.create(scheduled_at=self.td_start)
        es = p.experiencesample_set.create(scheduled_at=self.early)
        p.status = "baseline"
        p.tropo_answer("19", self.early, t)
        es = p.experiencesample_set.get(pk=es.pk)
        self.assertEqual(0, t.things_said)
        self.assertIsNotNone(es.answered_at)

    def testExpEampleAnswer(self):
        p = self.p1
        t = mocks.Tropo()

        p.status = "baseline"
        es = p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_answer("19", self.early, t)
        es = p.experiencesample_set.get(pk=es.pk)
        self.assertIsNotNone(es.answered_at)

        p.status = "game_inter_sample"
        p.experiencesample_set.all().delete()
        es = p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_answer("19", self.early, t)
        es = p.experiencesample_set.get(pk=es.pk)
        self.assertIsNotNone(es.answered_at)

        p.status = "game_post_sample"
        p.experiencesample_set.all().delete()
        es = p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_answer("19", self.early, t)
        es = p.experiencesample_set.get(pk=es.pk)
        self.assertIsNotNone(es.answered_at)

    def testAnswerChangesToGameGuess(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = 'game_permission'
        p.gamepermission_set.create(scheduled_at=self.early)
        p.tropo_answer("n", self.early, t, True)
        self.assertEqual("game_permission", p.status)
        self.assertEqual(0, p.hilowgame_set.count())
        p.gamepermission_set.create(scheduled_at=self.early)
        p.tropo_answer("y", self.early, t, True)
        self.assertEqual("game_guess", p.status)
        self.assertEqual(1, p.hilowgame_set.count())

    def testAnswerChangesToGameIntersample(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = 'game_guess'
        p.hilowgame_set.create(scheduled_at=self.early)
        p.tropo_answer("low", self.early, t, True)
        self.assertEqual('game_inter_sample', p.status)

    def testAnswerStopMessageSetsStopped(self):
        p = self.p1
        t = mocks.Tropo()
        p.tropo_answer("STOP", self.early, t, True)
        self.assertTrue(p.stopped)

    def testAnswerWithIncomingTextObject(self):
        p = self.p1
        t = mocks.Tropo()
        msg = models.IncomingTextMessage(message_text="19")
        p.status = "baseline"
        es = p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_answer(msg, self.early, t, True)
        es = p.experiencesample_set.get(pk=es.pk)
        self.assertIsNotNone(es.answered_at)

    def testFailedPermissionAnswerDoesntChangeStatus(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = 'game_permission'
        p.gamepermission_set.create(scheduled_at=self.early)
        p.tropo_answer("", self.early, t, True)
        self.assertEqual("game_permission", p.status)

    def testFailedGuessAnswerDoesntChangeStatus(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = 'game_guess'
        p.hilowgame_set.create(scheduled_at=self.early)
        p.tropo_answer("", self.early, t, True)
        self.assertEqual('game_guess', p.status)

    def testSendingClearsNextContactTime(self):
        p = self.p1
        t = mocks.Tropo()
        p.next_contact_time=self.early
        p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_send_message(self.early, t, True)
        self.assertIsNone(p.next_contact_time)

    def testSendingChangesStatusFromIntersampleToResult(self):
        p = self.p1
        p.status = "game_inter_sample"
        t = mocks.Tropo()
        p.next_contact_time=self.early
        p.experiencesample_set.create(scheduled_at=self.early)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual('game_result', p.status)
        self.assertEqual(t.called, p.phone_number.for_tropo)
        self.assertEqual(1, t.things_said)

    def testSendingChangesStatusFromResultToPostSample(self):
        p = self.p1
        p.status = "game_result"
        t = mocks.Tropo()
        p.next_contact_time=self.early
        p.hilowgame_set.create(scheduled_at=self.early)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual('game_post_sample', p.status)
        self.assertIsNotNone(p.hilowgame_set.newest().result_reported_at)
        self.assertEqual(t.called, p.phone_number.for_tropo)
        self.assertEqual(1, t.things_said)

    def testSendingChangesStatusFromPostSampleToBaseline(self):
        p = self.p1
        p.status = "game_post_sample"
        t = mocks.Tropo()
        hlg = p.hilowgame_set.create(
            scheduled_at=self.early,
            answered_at=self.early,
            result_reported_at=self.early)
        es = p.experiencesample_set.create(
            scheduled_at=self.early)
        later = self.early+datetime.timedelta(minutes=120)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual('game_post_sample', p.status)
        self.assertEqual(1, t.things_said)
        self.assertEqual(t.called, p.phone_number.for_tropo)

        later = self.early+datetime.timedelta(minutes=120)
        p.tropo_send_message(later, t, True)
        self.assertEqual('baseline', p.status)
        self.assertEqual(2, t.things_said)

    def testSendingWithoutGameReturnsToBaseline(self):
        p = self.p1
        t = mocks.Tropo()

        p.status = "game_result"
        p.tropo_send_message(self.early, t, True)
        self.assertEqual(0, t.things_said)
        self.assertEqual("baseline", p.status)

        p.status = "game_post_sample"
        p.tropo_send_message(self.early, t, True)
        self.assertEqual(1, t.things_said)
        self.assertEqual("baseline", p.status)

    def testBaselineMessageSends(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = "baseline"
        p.tropo_send_message(self.early, t, True)
        es = p.experiencesample_set.newest()
        self.assertEqual(1, t.things_said)
        self.assertEqual(t.called, p.phone_number.for_tropo)
        self.assertIsNotNone(es.sent_at)

    def testGamePermissionSends(self):
        p = self.p1
        t = mocks.Tropo()
        gp = p.gamepermission_set.create(scheduled_at=self.early)
        p.status = "game_permission"
        p.tropo_send_message(self.early, t, True)
        gp = p.gamepermission_set.get(pk=gp.pk)
        self.assertEqual(1, t.things_said)
        self.assertIsNotNone(gp.sent_at)

    def testGameGuessSends(self):
        p = self.p1
        t = mocks.Tropo()
        g = p.hilowgame_set.create(scheduled_at=self.early)
        p.status = "game_guess"
        p.tropo_send_message(self.early, t, True)
        g = p.hilowgame_set.get(pk=g.pk)
        self.assertEqual(1, t.things_said)
        self.assertIsNotNone(g.sent_at)

    def testGCUSSetsNCTGamePermission(self):
        p = self.p1
        p.status = "game_permission"
        g = p.gamepermission_set.create(scheduled_at=self.early)
        p.generate_contacts_and_update_status(self.early)
        self.assertIsNotNone(p.next_contact_time)

    def testGCUSSetsNCTGameIntersample(self):
        p = self.p1
        p.status = "game_inter_sample"
        p.generate_contacts_and_update_status(self.early)
        self.assertIsNotNone(p.next_contact_time)

    def testExpSamplesAreNotReused(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = "baseline"
        p.generate_contacts_and_update_status(self.early)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual(1, p.experiencesample_set.all().count())
        self.assertEqual(1, t.things_said)
        self.assertIsNone(p.next_contact_time)
        p.generate_contacts_and_update_status(self.td_start)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual(2, p.experiencesample_set.all().count())
        self.assertEqual(2, t.things_said)

    def testDoesNotSendWhileStopped(self):
        p = self.p1
        t = mocks.Tropo()
        p.status = "baseline"
        p.stopped = True
        p.generate_contacts_and_update_status(self.early)
        p.tropo_send_message(self.early, t, True)
        self.assertEqual(0, t.things_said)

    def testMessageCountAndBonusCount(self):
        p = self.p1
        ontime = self.early
        late = ontime+datetime.timedelta(seconds=self.exp.response_window+1)
        p.experiencesample_set.create(sent_at=ontime, answered_at=ontime)
        p.gamepermission_set.create(sent_at=ontime, answered_at=ontime)
        p.hilowgame_set.create(sent_at=ontime, answered_at=ontime)
        p.experiencesample_set.create(sent_at=ontime, answered_at=late)
        p.gamepermission_set.create(sent_at=ontime, answered_at=late)
        p.hilowgame_set.create(sent_at=ontime, answered_at=late)
        p.experiencesample_set.create(sent_at=ontime)

        self.assertEqual(7, p.message_count())
        self.assertEqual(3, p.message_count_for_bonus())

        self.assertAlmostEqual((float(3)/float(7)*100), p.bonus_fraction())

    def testQualifiesForBonus(self):
        p = self.p1
        ontime = self.early
        late = ontime+datetime.timedelta(seconds=self.exp.response_window+1)
        p.experiencesample_set.create(sent_at=ontime, answered_at=ontime)
        p.gamepermission_set.create(sent_at=ontime, answered_at=ontime)
        p.hilowgame_set.create(sent_at=ontime, answered_at=ontime)
        p.experiencesample_set.create(sent_at=ontime, answered_at=late)
        p.gamepermission_set.create(sent_at=ontime, answered_at=late)
        p.hilowgame_set.create(sent_at=ontime, answered_at=late)
        p.experiencesample_set.create(sent_at=ontime)

        p.experiment.min_pct_answered_for_bonus = 45
        p.experiment.save()
        self.assertFalse(p.qualifies_for_bonus())
        self.assertEqual(0, p.bonus_payout())

        p.experiment.min_pct_answered_for_bonus = 40
        p.experiment.save()
        self.assertTrue(p.qualifies_for_bonus())
        self.assertEqual(p.experiment.bonus_value, p.bonus_payout())

    def testWonGameCount(self):
        p = self.p1
        t1 = self.early
        p.hilowgame_set.create(sent_at=t1, correct_guess=1, guessed_low=True)
        p.hilowgame_set.create(sent_at=t1, correct_guess=1, guessed_low=False)
        p.hilowgame_set.create(sent_at=t1, correct_guess=9, guessed_low=True)
        p.hilowgame_set.create(sent_at=t1, correct_guess=9, guessed_low=False)
        self.assertEqual(2, p.won_game_count())

    def testTotalWonInGames(self):
        p = self.p1
        t1 = self.early
        p.hilowgame_set.create(sent_at=t1, correct_guess=1, guessed_low=True)
        p.hilowgame_set.create(sent_at=t1, correct_guess=1, guessed_low=False)
        self.assertEqual(self.exp.game_value, p.game_payout())

    def testTotalPayout(self):
        p = self.p1
        t1 = self.early
        p.hilowgame_set.create(
            sent_at=t1, answered_at=t1, correct_guess=1, guessed_low=True)
        p.hilowgame_set.create(
            sent_at=t1, answered_at=t1, correct_guess=1, guessed_low=False)
        total_amount = (
            p.experiment.participation_value +
            p.experiment.game_value +
            p.experiment.bonus_value)
        self.assertEqual(total_amount, p.total_payout())


class ExperienceSampleTest(TestCase):

    def setUp(self):
        self.today = datetime.date(2011, 7, 1)
        self.now = datetime.datetime(2011, 7, 1, 9, 30)
        self.later = datetime.datetime(2011, 7, 1, 3, 30)
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today,
            phone_number='6085551212')

        self.es = self.p1.experiencesample_set.create(scheduled_at=self.now)

    def testAnswerSetsAnsweredAt(self):
        self.es.answer("15", self.later, True)
        self.assertEqual(self.later, self.es.answered_at)

    def testAnswerGoodSetsPosNeg(self):
        corr = ('1', '5')
        self.es.answer("15", self.later, True)
        self.assertEqual(corr, self.es.val_tuple)
        self.es.answer("1 5", self.later, True)
        self.assertEqual(corr, self.es.val_tuple)
        self.es.answer(" 1 5 ", self.later, True)
        self.assertEqual(corr, self.es.val_tuple)
        self.es.answer("asd1asdas5asdas", self.later, True)
        self.assertEqual(corr, self.es.val_tuple)

    def testAnswerFailuresRaiseError(self):
        err = models.ResponseError
        self.assertRaises(err, self.es.answer, "", self.later, True)
        self.assertRaises(err, self.es.answer, "123", self.later, True)
        self.assertRaises(err, self.es.answer, "1", self.later, True)
        self.assertRaises(err, self.es.answer, "a", self.later, True)

    def testDeletedAtExcludesFromNewest(self):
        self.assertEqual(self.es, models.ExperienceSample.objects.newest())
        self.assertEqual(self.es, models.ExperienceSample.objects.active()[0])
        self.es.deleted_at = self.now
        self.es.save()
        self.assertIsNone(models.ExperienceSample.objects.newest())

    def testMarkSent(self):
        es = self.es
        self.assertNotEqual(self.p1.status, es.participant_status_when_sent)
        es.mark_sent(self.later, True)
        self.assertEqual(self.later, es.sent_at)
        self.assertEqual(self.p1.status, es.participant_status_when_sent)


class GamePermissionTest(TestCase):

    def setUp(self):
        self.now = datetime.datetime(2011, 7, 1, 9, 30)
        self.gp = models.GamePermission()

    def testAnswerWithYN(self):
        self.assertFalse(self.gp.permissed)
        self.gp.answer("y", self.now, True)
        self.assertTrue(self.gp.permissed)
        self.gp.answer("n", self.now, True)
        self.assertFalse(self.gp.permissed)
        self.gp.answer("Y", self.now, True)
        self.assertTrue(self.gp.permissed)
        self.gp.answer("N", self.now, True)
        self.assertFalse(self.gp.permissed)
        self.gp.answer(" y1 ", self.now, True)
        self.assertTrue(self.gp.permissed)
        self.gp.answer("0n0", self.now, True)
        self.assertFalse(self.gp.permissed)
        self.assertIsNotNone(self.gp.answered_at)

    def testBadAnswer(self):
        err = models.ResponseError
        self.assertRaises(err, self.gp.answer, "", self.now, True)
        self.assertRaises(err, self.gp.answer, "foo", self.now, True)
        self.assertIsNone(self.gp.answered_at)


class HiLowGameTest(TestCase):

    def setUp(self):
        self.now = datetime.datetime(2011, 7, 1, 9, 30)
        self.hlg = models.HiLowGame()

    def testGeneratesDefault(self):
        self.assertIsNotNone(self.hlg.correct_guess)

    def testAnswerWithNumber(self):
        hlg = self.hlg
        self.assertIsNone(hlg.guessed_low)
        hlg.answer('high', self.now, True)
        self.assertFalse(hlg.guessed_low)
        hlg.answer('low', self.now, True)
        self.assertTrue(hlg.guessed_low)
        hlg.answer('H', self.now, True)
        self.assertFalse(hlg.guessed_low)
        hlg.answer('L', self.now, True)
        self.assertTrue(hlg.guessed_low)
        self.assertIsNotNone(hlg.answered_at)

    def testBadAnswer(self):
        err = models.ResponseError
        self.assertRaises(err, self.hlg.answer, "", self.now, True)
        self.assertRaises(err, self.hlg.answer, "foo", self.now, True)
        self.assertIsNone(self.hlg.answered_at)

    def testGuessWasCorrect(self):
        hlg = self.hlg
        hlg.correct_guess = 1
        hlg.answer("low", self.now, True)
        self.assertTrue(hlg.guess_was_correct)
        hlg.answer("high", self.now, True)
        self.assertFalse(hlg.guess_was_correct)
        hlg.correct_guess = 9
        hlg.answer("high", self.now, True)
        self.assertTrue(hlg.guess_was_correct)
        hlg.answer("low", self.now, True)
        self.assertFalse(hlg.guess_was_correct)


class IncomingTextTest(TestCase):

    def setUp(self):
        self.today = datetime.date(2011, 7, 1)
        self.now = datetime.datetime(2011, 7, 1, 9, 30)
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today,
            phone_number='6085551212')

    def testStringRepresentation(self):
        msg = "I was once a kitten"
        tm = models.IncomingTextMessage(
            participant=self.p1,
            phone_number=self.p1.phone_number,
            message_text=msg,
            tropo_json="foo")
        self.assertEqual(msg, str(tm))


class PhoneNumberTest(TestCase):

    def testCreation(self):
        num = "6085551212"
        ph = models.PhoneNumber(num)
        self.assertEqual(num, ph.cleaned)

    def testStripNonNumeric(self):
        num = " 608555asjdha!dna1#}(212 "
        cleaned = "6085551212"
        ph = models.PhoneNumber(num)
        self.assertEqual(cleaned, ph.cleaned)

    def testStripLeadingOne(self):
        num = " 16085551212"
        cleaned = "6085551212"
        ph = models.PhoneNumber(num)
        self.assertEqual(cleaned, ph.cleaned)

    def testSaveOriginalString(self):
        num = "6085551212sldfkdsfj"
        ph = models.PhoneNumber(num)
        self.assertEqual(num, ph.original_string)

    def testDontFormatOddLengths(self):
        num = "55512"
        ph = models.PhoneNumber(num)
        self.assertEqual(num, str(ph))

    def testDoSevenDigitFormatting(self):
        num = "5551212"
        formatted = "555-1212"
        ph = models.PhoneNumber(num)
        self.assertEqual(formatted, str(ph))

    def testDoTenDigitFormatting(self):
        num = "6085551212"
        formatted = "(608) 555-1212"
        ph = models.PhoneNumber(num)
        self.assertEqual(formatted, str(ph))

    def testTropoFormatting(self):
        num = "6085551212"
        formatted = "16085551212"
        ph = models.PhoneNumber(num)
        self.assertEqual(formatted, ph.for_tropo)

    def testEqualty(self):
        num = "6085551212"
        p1 = models.PhoneNumber(num)
        p2 = models.PhoneNumber(num)
        self.assertEqual(p1, p2)


class TaskDayTest(TestCase):

    def setUp(self):
        self.today = datetime.date(2011, 7, 1) # Not really today.
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today, status='baseline')
        self.early = datetime.datetime(2011, 7, 1, 8, 30)
        self.td_start = datetime.datetime(2011, 7, 1, 9, 30)
        self.td_end = datetime.datetime(2011, 7, 1, 19, 00)
        self.late = datetime.datetime(2011, 7, 1, 20, 00)
        self.td1 = self.p1.taskday_set.create(
            task_day=self.td_start.date(),
            start_time=self.td_start.time(),
            end_time=self.td_end.time())

    def testCantCreateTaskDayTwice(self):
        with self.assertRaises(IntegrityError):
            td2 = self.p1.taskday_set.create(task_day=self.today)

    def testEarliestLatestContactsSave(self):
        self.assertEqual(self.td1.earliest_contact, self.td_start)
        self.assertEqual(self.td1.latest_contact, self.td_end)

    def testValidatesStatus(self):
        with self.assertRaises(ValidationError):
            self.td1.status = "sillier"
            self.td1.save()

    def testStatusForTimeGetsSetProperly(self):
        self.assertEqual('waiting', self.td1.status)
        self.td1.set_status_for_time(self.early)
        self.assertEqual('waiting', self.td1.status)
        self.td1.set_status_for_time(self.td_start)
        self.assertEqual('active', self.td1.status)
        self.td1.set_status_for_time(self.td_end)
        self.assertEqual('complete', self.td1.status)

    def testWaitingManagerWorks(self):
        tdset = models.TaskDay.waiting.all()
        self.assertEqual(self.td1, tdset[0])
        tdset = models.TaskDay.waiting.for_datetime(self.td_start)
        self.assertEqual(self.td1, tdset[0])

    def testActiveManagerWorks(self):
        models.TaskDay.objects.update(status='active')
        tdset = models.TaskDay.active.all()
        self.assertEqual(self.td1, tdset[0])
        tdset = models.TaskDay.active.expiring(self.late)
        self.assertEqual(self.td1, tdset[0])

    def testEndDaySetsStatusAndClearsPptNct(self):
        models.TaskDay.objects.update(status='active')
        models.Participant.objects.update(next_contact_time=self.late)
        self.td1.end_day(self.late)
        td = models.TaskDay.objects.get(pk=self.td1.pk)
        ppt = td.participant
        self.assertEqual('complete', td.status)
        self.assertIsNone(ppt.next_contact_time)
        self.assertEqual('complete', ppt.status)

    def testIsLastTaskDay(self):
        tomorrow = datetime.date(2011, 7, 2)
        td2 = self.p1.taskday_set.create(
            task_day=tomorrow,
            start_time=self.td_start.time(),
            end_time=self.td_end.time())
        self.assertFalse(self.td1.is_last_task_day())
        self.assertTrue(td2.is_last_task_day())

    def testStartDayCreatesGame(self):
        self.td1.is_game_day = True
        self.td1.save()
        self.assertEqual(0, self.p1.gamepermission_set.count())
        self.td1.start_day(self.td_start)
        self.assertEqual(1, self.p1.gamepermission_set.count())


class TropoRequestTest(TestCase):

    def setUp(self):
        self.change_settings_var('TROPO_PATH_PARAM', 'path')
        self.change_settings_var('TROPO_INCOMING_TEXT_PATH', '/incoming/')

        self.raw_incoming_sms = r"""{
"session": {
    "from": {
        "network": "SMS",
        "id": "16084486677",
        "channel": "TEXT",
        "name": null
    },
    "to": {
        "network": "SMS",
        "id": "16086164697",
        "channel": "TEXT",
        "name": null
    },
    "timestamp": "2011-07-25T18:01:28.926Z",
    "initialText": "One more",
    "headers": {
        "Content-Length": "124",
        "Via": "SIP/2.0/UDP 10.6.93.101:5066;branch=z9hG4bKcc4dhy",
        "From": "<sip:689C26C0-0EEA-4640-A830B7A21BF03950@10.6.61.201;channel=private;user=16084486677;msg=One%20more;network=SMS;step=2>;tag=t1m87o",
        "To": "<sip:9996127024@10.6.69.204:5061;to=16086164697>",
        "Contact": "<sip:10.6.93.101:5066;transport=udp>",
        "CSeq": "1 INVITE",
        "Call-ID": "w0leo4",
        "Max-Forwards": "70",
        "Content-Type": "application/sdp"
    },
    "userType": "HUMAN",
    "callId": "1b5d038d090d913b1856d77a2a06cd85",
    "id": "8fe3744201a2600b844751853db86933",
    "accountId": "62371"
}
}"""
        self.sms_request = views.TropoRequest(self.raw_incoming_sms)
        self.raw_incoming_session = r"""{
"session": {
    "parameters": {
        "path": "/test/",
        "format": "json",
        "pk": "1"
    },
    "timestamp": "2011-07-27T21:31:21.724Z",
    "initialText": null,
    "userType": "NONE",
    "callId": null,
    "id": "5aa1039bb972f8f8e9d5beaf5cc70262",
    "accountId": "62371"
}
}"""
        self.session_request = views.TropoRequest(self.raw_incoming_session)

    def testRawDataSetting(self):
        self.assertEqual(
            self.raw_incoming_sms, self.sms_request.raw_data)
        self.assertEqual(
            self.raw_incoming_session, self.session_request.raw_data)

    def testMethodSetting(self):
        self.assertEqual("POST", self.session_request.method)
        self.assertEqual("TEXT", self.sms_request.method)

    def testSetsParams(self):
        self.assertIsNotNone(self.session_request.REQUEST)
        self.assertIsNotNone(self.sms_request.REQUEST)
        self.assertEqual("1", self.session_request.REQUEST['pk'])

    def testTextsGenerateToFrom(self):
        self.assertIsNotNone(self.sms_request.call_to)
        self.assertIsNotNone(self.sms_request.call_from)

    def testTextsGeneratePhoneNumbers(self):
        from_num = models.PhoneNumber("16084486677")
        to_num = models.PhoneNumber("16086164697")
        self.assertEqual(from_num, self.sms_request.call_from['phone_number'])
        self.assertEqual(to_num, self.sms_request.call_to['phone_number'])

    def testIncomingText(self):
        self.assertEqual(self.sms_request.text_content, "One more")

    def change_settings_var(self, var_name, new_value):
        if not hasattr(self, "old_settings"):
            self.old_settings = {}
        try:
            self.old_settings[var_name] = getattr(settings, var_name)
        except:
            pass
        setattr(settings, var_name, new_value)

    def restore_settings_var(self, var_name):
        try:
            setattr(settings, var_name, self.old_settings[var_name])
        except:
            delattr(settings, var_name)

    def tearDown(self):
        self.restore_settings_var('TROPO_PATH_PARAM')
        self.restore_settings_var('TROPO_INCOMING_TEXT_PATH')


class IncludesValidatorTest(TestCase):

    def setUp(self):
        self.iv = validators.IncludesValidator(('foo', 'bar'))

    def testIVReturnsCallable(self):
        self.assertTrue(hasattr(self.iv, '__call__'))

    def testIVRaisesForFail(self):
        with self.assertRaises(ValidationError):
            self.iv('baz')

    def testIVDoesNotRaiseForSuccess(self):
        self.assertIsNone(self.iv('foo'))


class TextingTropoTest(TestCase):

    def setUp(self):
        self.exp = models.Experiment.objects.create(max_messages_per_day=1)
        self.today = datetime.date(2011, 7, 1)
        self.p1 = models.Participant.objects.create(
            experiment=self.exp,
            start_date=self.today,
            phone_number='6085551212')
        self.early = datetime.datetime(2011, 7, 1, 8, 30)

    def testDoesNotSendWhenParticipantIsStopped(self):
        p = self.p1
        t = mocks.Tropo()
        p.stopped = True
        t.send_text_to(p, self.early, "Woo")
        self.assertEqual(0, t.things_said)
        t.say_to(p, self.early, "Wham")
        self.assertEqual(0, t.things_said)

    def testSendToGeneratesOutgoingTextMessage(self):
        p = self.p1
        t = mocks.Tropo()
        t.send_text_to(p, self.early, "Woo")
        self.assertEqual(1, p.outgoingtextmessage_set.count())

    def testSayToGeneratesOutgoingTextMessage(self):
        p = self.p1
        t = mocks.Tropo()
        t.say_to(p, self.early, "Woo")
        self.assertEqual(1, p.outgoingtextmessage_set.count())

    def testDoesntSendTooManyMessages(self):
        p = self.p1
        t = mocks.Tropo()
        self.assertTrue(t.say_to(p, self.early, "Woo"))
        self.assertFalse(t.say_to(p, self.early, "Woo"))
        self.assertEqual(1, t.things_said)
        self.assertEqual(1, p.outgoingtextmessage_set.count())


class SecheduleAndSendTest(TestCase):

    def setUp(self):
        self.today = datetime.date(2011, 7, 1) # Not really today.
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today,
            phone_number='6085551212')
        self.today = datetime.date(2011, 7, 1)
        self.tomorrow = datetime.date(2011, 7, 2)
        self.start_time = datetime.time(8, 30)
        self.end_time = datetime.time(19, 00)
        self.td1 = self.p1.taskday_set.create(
            task_day=self.today,
            start_time=self.start_time,
            end_time=self.end_time)
        self.td2 = self.p1.taskday_set.create(
            task_day=self.tomorrow,
            start_time=self.start_time,
            end_time=self.end_time)
        self.cmd = schedule_and_send_messages.Command()

    def opts(self, *args, **kwargs):
        defaults = {
            'now': self.td1.earliest_contact,
            'tropo_reqester': mocks.OutgoingTropoSession()}

        defaults.update(kwargs)
        return defaults

    def testCommandRuns(self):
        self.cmd.handle_noargs(**self.opts())

    def testSetsPptNextContactTime(self):
        self.assertIsNone(self.p1.next_contact_time)
        self.cmd.handle_noargs(**self.opts())
        p = models.Participant.objects.get(pk=self.p1.pk)
        self.assertIsNotNone(p.next_contact_time)

    def testWakeupSleepAndComplete(self):
        pf = models.Participant.objects.get
        self.assertEqual(self.p1.status, "sleeping")
        self.cmd.handle_noargs(**self.opts())
        p = pf(pk=self.p1.pk)
        self.assertEqual(p.status, "baseline")

        self.cmd.handle_noargs(**self.opts(now=self.td1.latest_contact))
        p = pf(pk=self.p1.pk)
        self.assertEqual(p.status, "sleeping")

        self.cmd.handle_noargs(**self.opts(now=self.td2.earliest_contact))
        p = pf(pk=self.p1.pk)
        self.assertEqual(p.status, "baseline")

        self.cmd.handle_noargs(**self.opts(now=self.td2.latest_contact))
        p = pf(pk=self.p1.pk)
        self.assertEqual(p.status, "complete")

    def testGoToSleepDeletesOutstandingPermissions(self):
        p = self.p1
        t1 = self.td1.earliest_contact
        p.gamepermission_set.create(scheduled_at=t1)
        p.go_to_sleep(t1, False, True)
        self.assertIsNone(p.gamepermission_set.newest())

    def testStartsGamePermission(self):
        p = self.p1
        pf = models.Participant.objects.get
        gp = p.gamepermission_set.create(
            scheduled_at=self.td1.earliest_contact)
        self.cmd.handle_noargs(**self.opts())
        p = pf(pk=self.p1.pk)
        self.assertEqual("game_permission", p.status)

    def testGameReturnsToBaseline(self):
        p = self.p1
        pf = models.Participant.objects.get
        p.status = "game_permission"
        p.save()
        gp = p.gamepermission_set.create(
            scheduled_at=self.td1.earliest_contact)
        not_quite_end = self.td1.latest_contact-datetime.timedelta(minutes=60)

        self.cmd.handle_noargs(**self.opts(now=not_quite_end))
        p = pf(pk=self.p1.pk)
        self.assertEqual("baseline", p.status)


class StopMessageText(TestCase):

    def testHandlesStopMessages(self):
        s = models.StopMessage()
        self.assertTrue(bool(s.is_stop_message("STOP")))
        self.assertTrue(bool(s.is_stop_message("stop")))
        self.assertTrue(bool(s.is_stop_message("END")))
        self.assertTrue(bool(s.is_stop_message("CANCEL")))
        self.assertTrue(bool(s.is_stop_message("UNSUBSCRIBE")))
        self.assertTrue(bool(s.is_stop_message("QUIT")))
        self.assertTrue(bool(s.is_stop_message("STOP_ALL")))

    def testHandlesNonStopMessages(self):
        s = models.StopMessage()
        self.assertFalse(bool(s.is_stop_message("19")))
        self.assertFalse(bool(s.is_stop_message("low")))
        self.assertFalse(bool(s.is_stop_message("y")))
