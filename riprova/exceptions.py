# -*- coding: utf-8 -*-


class RetryError(Exception):
    """
    Retry error raised by this library will be an instance of this class.

    Retry originated errors internally raised by `riprova` will be
    an instance of `RetryError` class.
    """


class MaxRetriesExceeded(RetryError):
    """
    Retry error raised when a maximum of retry attemps is exceeded.
    """


class RetryTimeoutError(RetryError):
    """"
    Custom retry timeout error.
    """
