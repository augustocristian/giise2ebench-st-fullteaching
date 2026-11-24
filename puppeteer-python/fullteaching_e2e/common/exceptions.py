"""Domain exceptions, ported from ``common/exception/*.java``."""


class ElementNotFoundException(Exception):
    """A course, entry, session or other element that should exist could not be found."""


class NotLoggedException(Exception):
    """An action needing a logged-in user was attempted without a session."""


class BadUserException(Exception):
    """A different user than the expected one is logged in."""
