from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import logging
logger = logging.getLogger("smsgame")

import datetime
import json
import csv

from . import models


def timefmt(dt):
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt


def tropo(request):
    logger.debug("Tropo request: "+request.raw_post_data)
    treq = TropoRequest(request.raw_post_data)
    logger.debug(treq.method)
    logger.debug(treq.REQUEST)

    if treq.is_incoming:
        logger.debug("Processing incoming message")
        return incoming_message(treq)
    else:
        logger.debug("Processing outgoing message")
        return outgoing_message(treq)


def incoming_message(request):
    t = models.TextingTropo()
    response = HttpResponse(content_type='application/json')
    logger.debug(request.call_from)
    num = request.call_from['phone_number']
    logger.debug("Incoming message from %s" % num)
    ppt = None
    try:
        ppt = models.Participant.objects.get(phone_number=num)
    except models.Participant.DoesNotExist:
        pass
    tm = models.IncomingTextMessage.objects.create(
        participant=ppt,
        phone_number=num,
        message_text=request.text_content,
        tropo_json=request.raw_data)
    logger.debug("Message: %s" % tm)

    if ppt is None:
        logger.debug("No participant found.")
        t.hangup()
        response.write(t.RenderJson())
        return response

    ppt.tropo_answer(tm, datetime.datetime.now(), t)
    response.write(t.RenderJson())
    return response


def outgoing_message(request):
    pk = request.REQUEST['pk']
    ppt = get_object_or_404(models.Participant, pk=pk)
    t = models.TextingTropo()
    response = HttpResponse(content_type='application/json')
    now = datetime.datetime.now()
    ppt.tropo_send_message(now, t)
    response.write(t.RenderJson())
    return response


def experiencesamples_csv(request, slug):
    experiment = get_object_or_404(models.Experiment, url_slug=slug)

    response = HttpResponse(content_type='text/csv')
    csv_out = csv.writer(response)
    columns = ['experiment', 'participant', 'sample_num', 'status', 'sent_at',
        'answered_at', 'positive', 'negative']
    csv_out.writerow(columns)
    for p in experiment.participant_set.all().order_by('created_at'):
        for es in p.experiencesample_set.all().order_by('pk'):
            try:
                row = [experiment.url_slug, p.pk, es.pk,
                    es.participant_status_when_sent, timefmt(es.sent_at),
                    timefmt(es.answered_at), es.positive_emotion,
                    es.negative_emotion]
                csv_out.writerow(row)
            except Exception as e:
                csv_out.writerow(['Error in sample %s: %s' % (es.pk, e)])
                logger.debug("Error! %s" % e)

    return response


def hilowgames_csv(request, slug):
    experiment = get_object_or_404(models.Experiment, url_slug=slug)

    response = HttpResponse(content_type='text/csv')
    csv_out = csv.writer(response)
    columns = ['experiment', 'participant', 'game_num', 'status', 'sent_at',
        'answered_at', 'reported_at', 'correct_answer', 'guessed_low',
        'was_correct']
    csv_out.writerow(columns)
    for p in experiment.participant_set.all().order_by('created_at'):
        for g in p.hilowgame_set.all().order_by('pk'):
            try:
                row = [experiment.url_slug, p.pk, g.pk,
                    g.participant_status_when_sent, timefmt(g.sent_at),
                    timefmt(g.answered_at), timefmt(g.result_reported_at),
                    g.correct_guess, g.guessed_low, g.guess_was_correct]
                csv_out.writerow(row)
            except Exception as e:
                csv_out.writerow(['Error in game %s: %s' % (g.pk, e)])
                logger.debug("Error! %s" % e)

    return response


class TropoRequest(object):
    """
    This class causes an incoming Tropo request to simulate an HttpRequest
    closely enough to be used in standard view functions.
    request.method will be POST for session responses, TEXT for incoming
    texts, and VOICE for incoming voice calls.

    The parameters will be available in request.REQUEST, and the full
    parsed request will be in request.data. The full, unparsed data will
    be in request.raw_data.

    A path should be available in request.path and request.path_info.
    In the case of session responses, it's found in:
    request.REQUEST[settings.TROPO_PATH_PARAM]
    In the case of incoming text/voice data, it's:
    settings.TROPO_INCOMING_TEXT_PATH
    """

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.data = json.loads(raw_data)
        self._s = self.data.get("session") or {}
        self.__set_method()
        self.__set_parameters()
        self.__set_to_from()
        self.__set_text_content()

    @property
    def is_incoming(self):
        return "to" in self._s

    def __set_method(self):
        self.method = "POST"
        to = self._s.get("to")
        if to and to.get("channel"):
            self.method = to.get("channel")

    def __set_parameters(self):
        self.REQUEST = self._s.get("parameters") or {}

    def __set_to_from(self):
        self.call_to = self._s.get("to") or {}
        self.call_from = self._s.get("from") or {}

        if self.call_to.get("id"):
            self.call_to["phone_number"] = models.PhoneNumber(
                self.call_to["id"])
        if self.call_from.get("id"):
            self.call_from["phone_number"] = models.PhoneNumber(
                self.call_from["id"])

    def __set_text_content(self):
        self.text_content = self._s.get("initialText")
