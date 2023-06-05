# -*- coding: utf-8 -*-
from .retry import retry
from .retrier import Retrier
from .backoff import Backoff
from .errors import ErrorWhitelist, ErrorBlacklist, add_whitelist_error
from .strategies import *  # noqa
from .async_retrier import AsyncRetrier  # noqa
from .exceptions import (RetryError, MaxRetriesExceeded,
                         RetryTimeoutError, NotRetriableError)


__author__ = 'Tomas Aparicio'
__license__ = 'MIT'

# Current package version
__version__ = '0.3.1'

# Explicit symbols to export
__all__ = (
    'retry',
    'Retrier',
    'Backoff',
    'AsyncRetrier',
    'ConstantBackoff',
    'FibonacciBackoff',
    'ExponentialBackOff',
    'ErrorWhitelist',
    'ErrorBlacklist',
    'add_whitelist_error',
    'RetryError',
    'MaxRetriesExceeded',
    'RetryTimeoutError',
    'NotRetriableError'
)
