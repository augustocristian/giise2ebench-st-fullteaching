# -*- coding: utf-8 -*-
"""Domain exceptions, ported from common/exception/*.java.

ExceptionsHelper.java (a stack-trace file/line lookup) is not ported: it worked
around Java's verbose assertion failures, and pytest's own traceback already
reports the failing file/line.
"""


class ElementNotFoundException(Exception):
    pass


class NotLoggedException(Exception):
    pass


class BadUserException(Exception):
    pass


class TimeOutException(Exception):
    pass
