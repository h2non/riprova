# -*- coding: utf-8 -*-
import pytest
from riprova import (ErrorWhitelist, ErrorBlacklist,
                     NotRetriableError, add_whitelist_error)


def test_error_whitelist():
    whitelist = ErrorWhitelist()
    assert type(ErrorWhitelist.WHITELIST) is set

    assert len(whitelist._list) > 4
    assert type(whitelist._list) is set
    assert whitelist._list is not ErrorWhitelist.WHITELIST

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
    (SystemExit(), False),
    (ImportError(), False),
    (ReferenceError(), False),
    (SyntaxError(), False),
    (KeyboardInterrupt(), False),
    (NotRetriableError(), False),
    (NoRetryError(), False),
    (ReferenceError(), False),
    (RetryError(), True),
    (Exception(), True),
    (RuntimeError(), True),
    (TypeError(), True),
    (ValueError(), True),
])
def test_error_whitelist_isretry(error, expected):
    assert ErrorWhitelist().isretry(error) is expected


def test_error_blacklist():
    blacklist = ErrorBlacklist()
    assert type(ErrorBlacklist.WHITELIST) is set

    assert len(blacklist._list) > 4
    assert type(blacklist._list) is set
    assert blacklist._list is not ErrorWhitelist.WHITELIST

    # Test setter
    blacklist.errors = (Exception, RuntimeError)

    # Test getter
    assert blacklist.errors == set([Exception, RuntimeError])

    # Test add()
    blacklist.add(BaseException, SystemExit)
    assert blacklist.errors == set([Exception, RuntimeError,
                                    BaseException, SystemExit])


@pytest.mark.parametrize("error,expected", [
    (SystemExit(), True),
    (ImportError(), True),
    (ReferenceError(), True),
    (SyntaxError(), True),
    (KeyboardInterrupt(), True),
    (NotRetriableError(), True),
    (NoRetryError(), True),
    (ReferenceError(), True),
    (RetryError(), False),
    (Exception(), False),
    (RuntimeError(), False),
    (TypeError(), False),
    (ValueError(), False),
])
def test_error_blacklist_isretry(error, expected):
    assert ErrorBlacklist().isretry(error) is expected


def test_add_whitelist_error():
    whitelist = ErrorWhitelist.WHITELIST.copy()

    assert len(ErrorWhitelist.WHITELIST) == len(whitelist)
    add_whitelist_error(AttributeError, EnvironmentError)

    assert len(ErrorWhitelist.WHITELIST) == len(whitelist) + 2


def test_add_whitelist_error_invalid():
    with pytest.raises(TypeError):
        add_whitelist_error(None)

    with pytest.raises(TypeError):
        add_whitelist_error(dict())
