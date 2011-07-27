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

    def testPptWakesUpOnTaskDay(self):
        p1 = self.p1
        p1.status = "waiting"
        p1.save()
        now = datetime.datetime(1,1,1,8,30)
        td = td1 = p1.taskday_set.create(
            task_day=self.today,
            start_time = now.time())
        p1.wake_up(td)
        self.assertEqual(p1.status, "baseline")


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

    def testCantCreateTaskDayTwice(self):
        td1 = self.p1.taskday_set.create(task_day=self.today)
        with self.assertRaises(IntegrityError):
            td2 = self.p1.taskday_set.create(task_day=self.today)

    def testEarliestLatestContactsSave(self):
        early = datetime.datetime(2011, 7, 1, 8, 30)
        late = datetime.datetime(2011, 7, 1, 20, 00)
        td1 = self.p1.taskday_set.create(
            task_day=early.date(),
            start_time=early.time(),
            end_time=late.time())
        self.assertEqual(td1.earliest_contact, early)
        self.assertEqual(td1.latest_contact, late)


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
