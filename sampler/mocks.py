import logging
logger = logging.getLogger("smsgame")


class OutgoingTropoSession(object):

    def __init__(self, *args, **kwargs):
        self.request_count = 0

    def request_session(self, options):
        self.request_count += 1
        logger.debug(
            "%s call: mocks.OutgoingTropoSession#request_session: %s" %
            (self.request_count, options))


class Tropo(object):

    def __init__(self, *arg, **kwargs):
        self.called = ''
        self.things_said = 0
        self.hangups = 0

    def call(self, number, *args, **kwargs):
        self.called = number

    def say(self, message):
        self.things_said += 1

    def hangup(self):
        self.hangups += 1

    def RenderJson(self):
        return '{}'

    def send_text_to(self, phone_number, message):
        self.call(phone_number, channel="TEXT")
        self.say(message)
        self.hangup()
