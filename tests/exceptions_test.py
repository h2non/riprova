# -*- coding: utf-8 -*-
from riprova import RetryError, MaxRetriesExceeded, RetryTimeoutError


def test_retry_error():
    assert isinstance(RetryError(), Exception)
    assert issubclass(RetryError, Exception)


def test_max_retries_error():
    assert isinstance(MaxRetriesExceeded(), Exception)
    assert issubclass(MaxRetriesExceeded, RetryError)


def test_retry_timeout_error():
    assert isinstance(RetryTimeoutError(), Exception)
    assert issubclass(RetryTimeoutError, RetryError)
