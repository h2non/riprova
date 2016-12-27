# -*- coding: utf-8 -*-
from .retry import retry
from .retrier import Retrier
from .backoff import Backoff
from .constants import PY_34
from .strategies import *  # noqa
from .exceptions import RetryError, MaxRetriesExceeded, RetryTimeoutError

__author__ = 'Tomas Aparicio'
__license__ = 'MIT'

# Current package version
__version__ = '0.1.2'

# Explicit symbols to export
__all__ = (
    'retry',
    'Retrier',
    'Backoff',
    'ConstantBackoff',
    'FibonacciBackoff',
    'ExponentialBackOff',
    'RetryError',
    'MaxRetriesExceeded',
    'RetryTimeoutError'
)


# Expose asynchronous retrier if running in Python +3.4
if PY_34:
    from .async_retrier import AsyncRetrier
    __all__ += ('AsyncRetrier',)
