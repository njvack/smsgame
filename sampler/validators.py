from django.core.exceptions import ValidationError


class IncludesValidator(object):
    code = 'invalid'

    def __init__(self, haystack, message=None, code=None):
        self.haystack = haystack
        self.message = message
        if code is not None:
            self.code = code

    def __call__(self, needle):
        if needle in self.haystack:
            return
        if self.message is None:
            self.message = "%s does not contain %s" % (
                str(self.haystack), str(needle))
        raise(ValidationError(self.message, code=self.code))
