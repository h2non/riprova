# -*- coding: utf-8 -*-
import time
import pytest
from riprova import ConstantBackoff, MaxRetriesExceeded
from riprova.constants import PY_34

try:
    import asyncio
    from riprova import AsyncRetrier
except:
    asyncio, AsyncRetrier = None, None

# Require Python 3.4+
python34 = pytest.mark.skipif(not PY_34, reason='requires Python 3.4+')

if PY_34:
    @pytest.fixture
    def coro():
        scope = {'calls': 0, 'times': 0}

        @asyncio.coroutine
        def task(x, y, foo=0):
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


@python34
def test_async_retrier_defaults():
    retrier = AsyncRetrier()
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout == 0
    assert retrier.on_retry is None
    assert retrier.evaluator is None
    assert retrier.sleep == asyncio.sleep
    assert isinstance(retrier.backoff, ConstantBackoff)


@python34
def test_async_retrier_custom():
    @asyncio.coroutine
    def sleep(): pass

    @asyncio.coroutine
    def on_retry(): pass

    @asyncio.coroutine
    def evaluator(): pass

    backoff = ConstantBackoff()
    retrier = AsyncRetrier(timeout=1000, on_retry=on_retry,
                           sleep_coro=sleep, evaluator=evaluator,
                           backoff=backoff)
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout == 1000
    assert retrier.on_retry is on_retry
    assert retrier.evaluator is evaluator
    assert retrier.sleep == sleep
    assert retrier.backoff == backoff


@python34
def test_async_retrier_assestion_error():
    with pytest.raises(AssertionError):
        AsyncRetrier(timeout='foo')
    with pytest.raises(AssertionError):
        AsyncRetrier(timeout=-1)


@python34
def test_async_retrier_run_success(MagicMock, coro):
    on_retry = MagicMock()
    retrier = AsyncRetrier(on_retry=on_retry)

    task = coro(0)
    res = run_coro(retrier.run(task, 2, 4, foo=6))
    assert res == 12

    assert retrier.attempts == 0
    assert retrier.error is None


@python34
def test_async_retrier_run_valid_retries(MagicMock, coro):
    task = coro(4)
    on_retry = MagicMock()

    retrier = AsyncRetrier(on_retry=on_retry)
    res = run_coro(retrier.run(task, 2, 4, foo=6))
    assert res == 12

    assert retrier.attempts == 3
    assert retrier.error is None


@python34
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


@python34
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


@python34
def test_async_retrier_cancelled_error(MagicMock, coro):
    on_retry = MagicMock()

    @asyncio.coroutine
    def coro(x):
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


@python34
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


@python34
def test_async_retrier_run_max_timeout(MagicMock, coro):
    on_retry = MagicMock()
    task = coro(10)

    retrier = AsyncRetrier(timeout=250, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=100))

    with pytest.raises(asyncio.TimeoutError):
        run_coro(retrier.run(task, 2, 4, foo=6))

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts >= 1
    assert retrier.attempts < 4
    assert isinstance(retrier.error, RuntimeError)


@python34
def test_async_retrier_istimeout():
    assert AsyncRetrier().istimeout(1234) is False

    now = int(time.time() * 1000) - 2000
    assert AsyncRetrier(timeout=1000).istimeout(now) is True


@python34
def test_async_retrier_context_manager(MagicMock, coro):
    on_retry = MagicMock()
    retrier = AsyncRetrier(timeout=250, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=100, retries=5))

    @asyncio.coroutine
    def run_context():
        assert (yield from retrier.__aenter__()) is retrier

        try:
            yield from retrier.run(coro(10), 2, 4, foo='bar')
        except:
            yield from retrier.__aexit__(None, None, None)
        else:
            raise AssertionError('must raise exception')

    run_coro(run_context())

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts >= 1
    assert retrier.attempts < 4
    assert isinstance(retrier.error, RuntimeError)
