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


class ParticipantTest(TestCase):

    def setUp(self):
        random.seed(0)
        self.today = datetime.date(2011, 7, 1) # Not really today.
        self.exp = models.Experiment.objects.create()
        self.p1 = models.Participant.objects.create(
            experiment=self.exp, start_date=self.today)

    def testSetPrelimContactTime(self):
        p1 = self.p1
        now = datetime.datetime(2011, 7, 1, 10, 30)
        self.assertIsNone(p1.next_contact_time)
        p1.set_preliminary_next_contact_time(now)
        self.assertLess(now, p1.next_contact_time) # Test ordering
        t1 = p1.next_contact_time
        p1.set_preliminary_next_contact_time(now)
        self.assertNotEqual(t1, p1.next_contact_time) # Test randomization

    def testPptDoesntAllowCrazyStatus(self):
        p1 = self.p1
        p1.status = "crazy"
        with self.assertRaises(ValidationError):
            p1.save()


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
            experiment=self.exp, start_date=self.today)
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
