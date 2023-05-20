# -*- coding: utf-8 -*-
import time
import pytest
from riprova import ConstantBackoff, MaxRetriesExceeded
from riprova.constants import PY_35

try:
    import asyncio
    from riprova import AsyncRetrier
except Exception as error:
    asyncio, AsyncRetrier = None, None


if PY_35:
    @pytest.fixture
    def coro():
        scope = {'calls': 0, 'times': 0}

        async def task(x, y, foo=0):
            scope['calls'] += 1
            if scope['calls'] < scope['times']:
                raise RuntimeError('invalid call')
            return x + y + foo

        def setup(times=0):
            scope['times'] = times
            return task

        return setup

    def run_coro(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
else:
    @pytest.fixture
    def coro():
        pass


@python35
def test_async_retrier_defaults():
    retrier = AsyncRetrier()
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout is None
    assert retrier.on_retry is None
    assert retrier.evaluator is None
    assert retrier.sleep == asyncio.sleep
    assert isinstance(retrier.backoff, ConstantBackoff)


def test_async_retrier_custom():
    async def sleep(): pass

    async def on_retry(): pass

    async def evaluator(): pass

    backoff = ConstantBackoff()
    retrier = AsyncRetrier(timeout=1, on_retry=on_retry,
                           sleep_coro=sleep, evaluator=evaluator,
                           backoff=backoff)
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout == 1
    assert retrier.on_retry is on_retry
    assert retrier.evaluator is evaluator
    assert retrier.sleep == sleep
    assert retrier.backoff == backoff


def test_async_retrier_assestion_error():
    with pytest.raises(AssertionError):
        AsyncRetrier(timeout='foo')
    with pytest.raises(AssertionError):
        AsyncRetrier(timeout=-1)


def test_async_retrier_run_success(MagicMock, coro):
    on_retry = MagicMock()
    retrier = AsyncRetrier(on_retry=on_retry)

    task = coro(0)
    res = run_coro(retrier.run(task, 2, 4, foo=6))
    assert res == 12

    assert retrier.attempts == 0
    assert retrier.error is None


def test_async_retrier_run_valid_retries(MagicMock, coro):
    task = coro(4)
    on_retry = MagicMock()

    retrier = AsyncRetrier(on_retry=on_retry)
    res = run_coro(retrier.run(task, 2, 4, foo=6))
    assert res == 12

    assert retrier.attempts == 3
    assert retrier.error is None


def test_async_retrier_evaluator(MagicMock, coro):
    on_retry = MagicMock()
    task = coro(4)

    def evaluator(x):
        if x < 4:
            raise ValueError('small number')
        return False

    retrier = AsyncRetrier(evaluator=evaluator, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=0, retries=10))

    res = run_coro(retrier.run(task, 2, 4, foo=6))
    assert res == 12

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert retrier.error is None


def test_async_retrier_evaluator_error_default(MagicMock, coro):
    on_retry = MagicMock()
    task = coro(4)

    def evaluator(x):
        if x < 4:
            raise ValueError('small number')
        raise ImportError('pass error')

    retrier = AsyncRetrier(evaluator=evaluator, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=0, retries=10))

    with pytest.raises(ImportError):
        run_coro(retrier.run(task, 2, 4, foo=6))

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert isinstance(retrier.error, ImportError)


def test_async_retrier_cancelled_error(MagicMock, coro):
    on_retry = MagicMock()

    async def coro(x):
        if on_retry.call_count < x:
            raise ValueError('small number')
        raise asyncio.CancelledError('oops')

    retrier = AsyncRetrier(on_retry=on_retry,
                           backoff=ConstantBackoff(interval=0, retries=10))

    with pytest.raises(asyncio.CancelledError):
        run_coro(retrier.run(coro, 4))

    assert on_retry.called
    assert on_retry.call_count == 4

    assert retrier.attempts == 5
    assert retrier.error is not None


def test_async_retrier_run_max_retries_error(MagicMock, coro):
    on_retry = MagicMock()
    task = coro(10)

    retrier = AsyncRetrier(on_retry=on_retry,
                           backoff=ConstantBackoff(interval=0, retries=2))

    with pytest.raises(MaxRetriesExceeded):
        run_coro(retrier.run(task, 2, 4, foo=6))

    assert on_retry.called
    assert on_retry.call_count == 2

    assert retrier.attempts == 2
    assert isinstance(retrier.error, RuntimeError)


def test_async_retrier_run_max_timeout(MagicMock, coro):
    on_retry = MagicMock()
    task = coro(10)

    retrier = AsyncRetrier(timeout=.25, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=.1))

    with pytest.raises(asyncio.TimeoutError):
        run_coro(retrier.run(task, 2, 4, foo=6))

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts >= 1
    assert retrier.attempts < 4
    assert isinstance(retrier.error, RuntimeError)


def test_async_retrier_istimeout():
    assert AsyncRetrier().istimeout(1234) is False

    now = time.time() - 100
    assert AsyncRetrier(timeout=1).istimeout(now) is True


def test_async_retrier_context_manager(MagicMock, coro):
    from .async_retrier_context import test_async_retrier_context_manager
    test_async_retrier_context_manager(MagicMock, coro, run_coro)
