# -*- coding: utf-8 -*-
import pytest
from riprova import ErrorWhitelist, NotRetriableError


def test_error_whitelist():
    whitelist = ErrorWhitelist()
    assert type(ErrorWhitelist.WHITELIST) is set

    assert len(whitelist._whitelist) > 4
    assert type(whitelist._whitelist) is set
    assert whitelist._whitelist is not ErrorWhitelist.WHITELIST

    # Test setter
    whitelist.errors = (Exception, RuntimeError)

    # Test getter
    assert whitelist.errors == set([Exception, RuntimeError])

    # Test add()
    whitelist.add(BaseException, SystemExit)
    assert whitelist.errors == set([Exception, RuntimeError,
                                    BaseException, SystemExit])


def test_error_whitelist_invalid():
    whitelist = ErrorWhitelist()

    with pytest.raises(TypeError):
        whitelist.errors = dict()

    with pytest.raises(TypeError):
        whitelist.errors = None

    with pytest.raises(TypeError):
        whitelist.add(None)

    with pytest.raises(TypeError):
        whitelist.add(dict())


class NoRetryError(NotRetriableError):
    pass


class RetryError(NotRetriableError):
    __retry__ = True


@pytest.mark.parametrize("error,expected", [
    (SystemExit(), True),
    (ImportError(), True),
    (ReferenceError(), True),
    (SyntaxError(), True),
    (KeyboardInterrupt(), True),
    (NotRetriableError(), True),
    (NoRetryError(), True),
    (RetryError(), False),
    (ReferenceError(), True),
    (Exception(), False),
    (RuntimeError(), False),
    (TypeError(), False),
    (ValueError(), False),
])
def test_error_whitelist_iswhitedlisted(error, expected):
    assert ErrorWhitelist().iswhitelisted(error) is expected
