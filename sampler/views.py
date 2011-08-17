from django.conf import settings
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import logging
logger = logging.getLogger("smsgame")

import datetime
import json

from tropo import Tropo

from . import models


def tropo(request):
    # This method will take an HttpRequest from Tropo, create a TropoRequest
    # object, and then route it using resolve()

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
    t = Tropo()
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
    t = Tropo()
    ppt.tropo_send_message()
    t.call(ppt.phone_number.for_tropo, channel="TEXT")
    t.hangup()
    response = HttpResponse(content_type='applicaion/json')
    response.write(t.RenderJson())
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
