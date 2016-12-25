# -*- coding: utf-8 -*-
import pytest
from riprova import ConstantBackoff


def test_constant_backoff_defaults():
    backoff = ConstantBackoff()
    assert backoff.retries == 10
    assert backoff.interval == 100
    assert backoff.pending_retries == backoff.retries


def test_constant_backoff_params():
    backoff = ConstantBackoff(interval=500, retries=5)
    assert backoff.retries == 5
    assert backoff.interval == 500
    assert backoff.pending_retries == backoff.retries


def test_constant_backoff():
    backoff = ConstantBackoff()
    assert backoff.retries == 10
    assert backoff.interval == 100

    delay = backoff.next()
    assert delay == backoff.interval
    assert backoff.pending_retries == backoff.retries - 1

    delay = backoff.next()
    assert delay == backoff.interval
    assert backoff.pending_retries == backoff.retries - 2

    backoff.reset()
    assert backoff.retries == 10
    assert backoff.interval == 100
    assert backoff.pending_retries == backoff.retries


def test_constant_backoff_max_retries():
    backoff = ConstantBackoff(retries=5)
    assert backoff.retries == 5
    assert backoff.interval == 100
    assert backoff.pending_retries == backoff.retries

    for i in range(5):
        backoff.next()
        assert backoff.pending_retries == backoff.retries - (i + 1)

    assert backoff.next() == backoff.STOP


def test_constant_backoff_validation():
    with pytest.raises(AssertionError):
        ConstantBackoff(retries='foo')
    with pytest.raises(AssertionError):
        ConstantBackoff(retries=-1)
    with pytest.raises(AssertionError):
        ConstantBackoff(interval='foo')
    with pytest.raises(AssertionError):
        ConstantBackoff(interval=-1)
