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
        self.things_said_list = []
        self.hangups = 0

    def call(self, number, *args, **kwargs):
        self.called = number

    def say(self, message):
        self.things_said += 1
        self.things_said_list.append(message)

    def hangup(self):
        self.hangups += 1

    def RenderJson(self):
        return '{}'

    def say_to(self, participant, dt, message):
        if not participant.can_send_texts_at(dt):
            logger.debug("say_to: %s can't get messages more at %s" %
                (participant, dt))
            return False
        self.say(message)

    def send_text_to(self, participant, dt, message):
        if not participant.can_send_texts_at(dt):
            logger.debug("send_text_to: %s can't get messages more at %s" %
                (participant, dt))
            return False
        self.call(participant.phone_number.for_tropo, channel="TEXT")
        self.say(message)
        self.hangup()
        return True
