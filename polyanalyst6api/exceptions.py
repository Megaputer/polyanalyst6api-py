"""
polyanalyst6api.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains polyanalyst6api specific Exception classes.
"""

__all__ = ['PAException', 'ClientException', 'APIException', 'PABusy']


class PAException(Exception):
    """Generic error class, catch-all for most polyanalyst6api issues."""


class APIException(PAException):
    """Indicate errors that involve responses from PolyAnalyst's API.

    :param msg: The exception message
    :param endpoint: The resource endpoint
    :param status_code: The http status code
    """

    def __init__(self, msg: str, endpoint: str = None, status_code: int = None):
        self.message = msg
        self.endpoint = endpoint
        self.status_code = status_code

    def __str__(self):
        return f'{self.message} ({self.status_code}, {self.endpoint})'


class PABusy(APIException):
    def __init__(self):
        super().__init__('')

    def __str__(self):
        return 'PolyAnalyst server is busy'


class ClientException(PAException):
    """Indicate errors that don't involve interaction with PolyAnalyst's API."""


class _WrapperNotFound(PAException):
    pass
