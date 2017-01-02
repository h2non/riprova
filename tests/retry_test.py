# -*- coding: utf-8 -*-
import pytest
import functools
from riprova.constants import PY_34
from riprova import retry, ConstantBackoff


def task(times):
    count = {'calls': 0}

    def wrapper(x):
        count['calls'] += 1

        if count['calls'] < times:
            raise RuntimeError('foo')

        return x * x
    return wrapper


def test_retry(MagicMock):
    on_retry = MagicMock()
    retrier = retry(on_retry=on_retry)(task(4))
    assert retrier(2) == 4
    assert on_retry.called
    assert on_retry.call_count == 3

    on_retry = MagicMock()
    retrier = retry(on_retry=on_retry, backoff=ConstantBackoff())(task(4))
    assert retrier(3) == 9
    assert on_retry.called
    assert on_retry.call_count == 3

    on_retry = MagicMock()
    retrier = retry(on_retry=on_retry, backoff=ConstantBackoff())(task(4))
    assert retrier(4) == 16
    assert on_retry.called
    assert on_retry.call_count == 3


def test_retry_decorator():
    count = {'calls': 0}

    @retry
    def task(x):
        count['calls'] += 1
        if count['calls'] < 4:
            raise RuntimeError('call error')
        return x * x

    assert task(2) == 4


@pytest.mark.skipif(not PY_34, reason='requires Python 3.4+')
def test_retry_async(MagicMock):
    import asyncio
    loop = asyncio.get_event_loop()

    # Track coro calls
    count = {'calls': 0}

    @asyncio.coroutine
    def coro(times, x):
        count['calls'] += 1

        if count['calls'] < times:
            raise RuntimeError('foo')

        return x * x

    on_retry = MagicMock()
    retrier = retry(on_retry=on_retry, backoff=ConstantBackoff(interval=.2,
                                                               retries=10))

    decorator = retrier(asyncio.coroutine(functools.partial(coro, 4)))
    result = loop.run_until_complete(decorator(2))
    assert result == 4

    assert on_retry.called
    assert on_retry.call_count == 3
