"""
polyanalyst6api.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains polyanlyst6api specific Exception classes.
"""


class PAException(Exception):
    """Generic error class, catch-all for most polyanalyst6api issues."""


class APIException(PAException):
    """Indicate errors that involve responses from PolyAnalyst's API.

    :param msg: The exception message
    :param endpoint: The resource endpoint
    :param status_code: The http status code
    """

    def __init__(self, msg: str, endpoint: str = None, status_code: int = None) -> None:
        self.message = msg
        self.endpoint = endpoint
        self.status_code = status_code

    def __str__(self):
        return f'{self.message} ({self.status_code}, {self.endpoint})'


class ClientException(PAException):
    """Indicate errors that don't involve interaction with PolyAnalyst's API."""
