# -*- coding: utf-8 -*-
import pytest
from riprova import FibonacciBackoff


def test_fibonacci_backoff_defaults():
    backoff = FibonacciBackoff()
    assert backoff.prev == 0
    assert backoff.retries == 0
    assert backoff.current == 1
    assert backoff.initial == 1
    assert backoff.max_retries == 10
    assert backoff.multiplier == 1


def test_fibonacci_backoff_params():
    backoff = FibonacciBackoff(initial=2, retries=5, multiplier=2)
    assert backoff.prev == 0
    assert backoff.retries == 0
    assert backoff.current == 2
    assert backoff.initial == 2
    assert backoff.max_retries == 5
    assert backoff.multiplier == 2


def test_fibonacci_backoff():
    backoff = FibonacciBackoff()
    assert backoff.retries == 0
    assert backoff.multiplier == 1
    assert backoff.max_retries == 10
    assert backoff.current == 1

    for i, n in enumerate([1, 2, 3, 5, 8, 13, 21]):
        delay = backoff.next()
        assert delay == n * backoff.multiplier
        assert backoff.retries == i + 1

    assert backoff.prev == 13
    assert backoff.retries == 7
    assert backoff.current == 21

    backoff.reset()
    assert backoff.prev == 0
    assert backoff.retries == 0
    assert backoff.current == 1


def test_fibonacci_backoff_max_retries():
    backoff = FibonacciBackoff(retries=5)
    assert backoff.retries == 0
    assert backoff.current == 1
    assert backoff.multiplier == 1
    assert backoff.max_retries == 5

    for i in range(5):
        backoff.next()
        assert backoff.retries == i + 1

    assert backoff.next() == backoff.STOP


def test_fibonacci_backoff_validation():
    with pytest.raises(AssertionError):
        FibonacciBackoff(retries='foo')
    with pytest.raises(AssertionError):
        FibonacciBackoff(retries=-1)
    with pytest.raises(AssertionError):
        FibonacciBackoff(initial='foo')
    with pytest.raises(AssertionError):
        FibonacciBackoff(initial=-1)
    with pytest.raises(AssertionError):
        FibonacciBackoff(multiplier=None)
    with pytest.raises(AssertionError):
        FibonacciBackoff(multiplier=-1)
