from django.http import HttpResponse

from tropo import Tropo

import logging
logger = logging.getLogger("smsgame")

def tropo(request):
    logger.debug(request.raw_post_data)

    t = Tropo()
    t.say("OK, got it.")
    t.hangup()
    response = HttpResponse(content_type='application/json')
    response.write(t.RenderJson())
    return response