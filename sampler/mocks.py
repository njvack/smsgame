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
