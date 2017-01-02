# -*- coding: utf-8 -*-
import asyncio
from riprova import AsyncRetrier, ConstantBackoff


def test_async_retrier_context_manager(MagicMock, coro, run_coro):
    on_retry = MagicMock()
    retrier = AsyncRetrier(timeout=.25, on_retry=on_retry,
                           backoff=ConstantBackoff(interval=.1, retries=5))

    @asyncio.coroutine
    def run_context():
        assert (yield from retrier.__aenter__()) is retrier  # noqa

        try:
            yield from retrier.run(coro(10), 2, 4, foo='bar')  # noqa
        except:
            yield from retrier.__aexit__(None, None, None)  # noqa
        else:
            raise AssertionError('must raise exception')

    run_coro(run_context())

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts >= 1
    assert retrier.attempts < 4
    assert isinstance(retrier.error, RuntimeError)
