# -*- coding: utf-8 -*-
from riprova import (RetryError, MaxRetriesExceeded,
                     RetryTimeoutError, NotRetriableError)


def test_retry_error():
    assert isinstance(RetryError(), Exception)
    assert issubclass(RetryError, Exception)


def test_max_retries_error():
    assert isinstance(MaxRetriesExceeded(), Exception)
    assert issubclass(MaxRetriesExceeded, RetryError)


def test_retry_timeout_error():
    assert isinstance(RetryTimeoutError(), Exception)
    assert issubclass(RetryTimeoutError, RetryError)


def test_not_retriable_error():
    assert isinstance(NotRetriableError(), Exception)
    assert not issubclass(NotRetriableError, RetryError)
    assert hasattr(NotRetriableError(), '__retry__')
    assert getattr(NotRetriableError(), '__retry__') is False
