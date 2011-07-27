from django.http import HttpResponse

from tropo import Tropo

import logging
logger = logging.getLogger("smsgame")

from . import models

def tropo(request):
    s = models.IncomingTropoSession(request.raw_post_data)
    ppt = models.Participant.objects.get(pk=s['parameters']['pk'])
    t = Tropo()
    t.call("1"+str(ppt.phone_number), channel='TEXT')
    t.say("OK, got it.")
    t.hangup()
    response = HttpResponse(content_type='application/json')
    response.write(t.RenderJson())
    return response