"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings

import random
import datetime

from . import models
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

    def testGenerateContactAt(self):
        delta = datetime.timedelta(minutes=1)
        now = self.td_start+delta
        self.p1.generate_contact_at(now)
        self.assertGreater(self.p1.experiencesample_set.count, 0)


class ExperienceSampleTest(TestCase):

    def setUp(self):
        self.today = datetime.date(2011, 7, 1)
        self.now = datetime.datetime(2011, 7, 1, 9, 30)
        self.later = datetime.datetime(2011, 7, 1, 3, 30)
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today,
            phone_number='6085551212')

        self.es = models.ExperienceSample(
            participant=self.p1,
            scheduled_at=self.now)

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
        self.assertRaises(models.ResponseError, self.es.answer,
            "", self.later, True)
        self.assertRaises(models.ResponseError, self.es.answer,
            "123", self.later, True)
        self.assertRaises(models.ResponseError, self.es.answer,
            "1", self.later, True)
        self.assertRaises(models.ResponseError, self.es.answer,
            "a", self.later, True)


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

    def testSetsPath(self):
        self.assertEqual("/test/", self.session_request.path)
        self.assertEqual("/test/", self.session_request.path_info)
        self.assertEqual(
            settings.TROPO_INCOMING_TEXT_PATH, self.sms_request.path)
        self.assertEqual(
            settings.TROPO_INCOMING_TEXT_PATH, self.sms_request.path_info)

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


class SecheduleAndSendTest(TestCase):

    def setUp(self):
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
        self.cmd = schedule_and_send_messages.Command()

    def test_command_runs(self):
        opts = {'now': self.td_start}
        self.cmd.handle_noargs(**opts)

    def test_sets_ppt_next_contact_time(self):
        self.assertIsNone(self.p1.next_contact_time)
        opts = {'now': self.td_start}
        self.cmd.handle_noargs(**opts)
        p = models.Participant.objects.get(pk=self.p1.pk)
        self.assertIsNotNone(p.next_contact_time)
