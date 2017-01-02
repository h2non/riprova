# -*- coding: utf-8 -*-
import pytest
from riprova import ExponentialBackOff


def test_exponential_backoff_defaults():
    backoff = ExponentialBackOff()
    assert backoff.started is None
    assert backoff.factor == 0.5
    assert backoff.multiplier == 1.5
    assert backoff.interval == 500
    assert backoff.max_interval == 60000
    assert backoff.max_elapsed == 15 * 60 * 1000
    assert backoff.current_interval == backoff.interval


def test_exponential_backoff_params():
    backoff = ExponentialBackOff(interval=2, factor=1.2,
                                 max_interval=1,
                                 max_elapsed=5,
                                 multiplier=2.5)
    assert backoff.started is None
    assert backoff.factor == 1
    assert backoff.multiplier == 2.5
    assert backoff.interval == 2000
    assert backoff.max_interval == 1000
    assert backoff.max_elapsed == 5000
    assert backoff.current_interval == backoff.interval


def test_exponential_backoff():
    interval, factor = 2, .5
    backoff = ExponentialBackOff(interval=interval, factor=factor)
    assert backoff.factor == factor
    assert backoff.interval == interval * 1000

    delay = backoff.next()
    assert delay in range(interval, interval + 10)
    assert backoff.current_interval == backoff.interval + 1000

    delay = backoff.next()
    assert delay in range(interval + int(interval * factor) - 5,
                          interval + int(interval * factor) + 5)
    assert backoff.current_interval == backoff.interval + 2500

    delay = backoff.next()
    assert delay >= 4.5 and delay <= 5.0
    assert backoff.current_interval == 6750.0

    delay = backoff.next()
    assert delay >= 6 and delay <= 7
    assert backoff.current_interval == 10125.0

    backoff.reset()
    assert backoff.started is None
    assert backoff.interval == interval * 1000
    assert backoff.current_interval == backoff.interval


def test_exponential_backoff_validation():
    with pytest.raises(AssertionError):
        ExponentialBackOff(factor='foo')
    with pytest.raises(AssertionError):
        ExponentialBackOff(factor=None)
    with pytest.raises(AssertionError):
        ExponentialBackOff(interval='foo')
    with pytest.raises(AssertionError):
        ExponentialBackOff(interval=-1)
    with pytest.raises(AssertionError):
        ExponentialBackOff(max_interval='foo')
    with pytest.raises(AssertionError):
        ExponentialBackOff(max_elapsed='foo')
    with pytest.raises(AssertionError):
        ExponentialBackOff(multiplier='foo')
    with pytest.raises(AssertionError):
        ExponentialBackOff(multiplier=-1)
