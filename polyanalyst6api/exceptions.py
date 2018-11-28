class PAException(Exception):
    """The base PolyAnalyst Exception that all other exception classes extend."""


class APIException(PAException):
    """Indicate exception that involve responses from PolyAnalyst's API."""

    def __init__(self, msg, endpoint=None, status_code=None):
        self._msg = msg
        self.endpoint = endpoint
        self.status_code = status_code

    def __str__(self):
        return f'{self._msg} ({self.status_code}, {self.endpoint})'


class ClientException(PAException):
    """Indicate exceptions that don't involve interaction with PolyAnalyst's API."""


class AuthException(PAException):
    """Indicate authorization error."""
