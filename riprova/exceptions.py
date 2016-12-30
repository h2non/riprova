# -*- coding: utf-8 -*-


class RetryError(Exception):
    """
    Retry error raised by this library will be an instance of this class.

    Retry originated errors internally raised by `riprova` will be
    an instance of `RetryError` class.
    """


class MaxRetriesExceeded(RetryError):
    """
    Retry error raised when a maximum of retry attemps is exceeded, reported
    by the backoff strategy being used.
    """


class RetryTimeoutError(RetryError):
    """"
    Custom retry timeout error internally used by `riprova` when a task
    exceeds the maximum time execution limit.
    """


class NotRetriableError(Exception):
    """"
    Utility error class that can be inherited by developers for those cases
    where the error should be ignored by `riprova` retry engine.

    Attributes:
        __retry__ (bool): optional magic attribute inferred by `riprova` in
            order to determine when an error should be retried or not.
            You can optionally flag any error exception with this magic
            attribute in order to modify the retry behaviour.
            Defaults to `False`.

    Usage::

        # Raised exception with the following ignored won't be retried
        # by riprova
        class MyWhiteListedError(riprova.NotRetriableError):
            pass

        # You can optionally reverse that behaviour for specific cases
        # by defining the `__retry__` magic attribute as `True`
        class MyWhiteListedError(riprova.NotRetriableError):
            __retry__ = True

    """
    __retry__ = False
