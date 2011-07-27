"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

import random
import datetime

from . import models
from . import validators


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
