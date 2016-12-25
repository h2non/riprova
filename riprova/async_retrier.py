# -*- coding: utf-8 -*-
from paco import wraps, TimeoutLimit
from .backoff import Backoff
from .retrier import Retrier
from .constants import PY_34
from .strategies import ConstantBackoff
from .exceptions import MaxRetriesExceeded, RetryError

# Ensure user do not import this module in unsupported Python runtimes
if not PY_34:  # pragma: no cover
    raise RuntimeError('cannot import async_retrier module in Python <= 3.4')

import asyncio  # noqa


class AsyncRetrier(Retrier):
    """
    AsyncRetrier implements an asynchronous corutine based operation retrier.

    Only compatible with `asyncio` in Python 3.4+.

    Arguments:
        timeout (int): maximum optional timeout in miliseconds.
            Use `0` for no limit. Defaults to `0`.
        backoff (riprova.Backoff): optional backoff strategy to use.
            Defaults to `riprova.ConstantBackoff`.
        evaluator (function): optional evaluator function used to determine
            when an operation should be retried or not.
            This allow the developer to retry operations that do not raised
            any exception, for instance. Evaluator function accepts 1
            argument: the returned task result.
            Evaluator function can raise an exception, return an error or
            simply return `True` in order to retry the operation.
            Otherwise the operation will be considered as valid and the
            retry loop will end.
        on_retry (function): optional function to call on before very retry
            operation. `on_retry` function accepts 2 arguments: `err, next_try`
            and should return nothing.
        sleep_coro (coroutinefunction): optional coroutine function used to
            sleep. Defaults to `asyncio.sleep`.

    Attributes:
        timeout (int): stores the maximum retries attempts timeout in
            milliseconds. Defaults to `0`.
        attempts (int): number of retry attempts being executed from last
            `run()` method call.
        error (Exception): stores the latest generated error.
            `None` if not error yet from last `run()` execution.
        sleep (coroutinefunction): stores the coroutine function used to sleep.
            Defaults to `asyncio.sleep`.
        backoff (Backoff): stores current used backoff.
            Defaults to `riprova.ConstantBackoff`.
        evaluator (coroutinefunction): stores the used evaluator function.
            Defaults to `None`.
        on_retry (coroutinefunction): stores the retry notifier function.
            Defaults to `None`.

    Raises:
        AssertionError: in case of invalid input params.

    Usage::

        retrier = riprova.AsyncRetrier(
            timeout=10 * 1000,
            backoff=riprova.FibonacciBackoff(retries=5))

        async def task(x):
            return x * x

        loop = asyncio.get_event_loop()

        result = loop.run_until_complete(retrier.run(task, 4))
        assert result == 16
        assert retrier.attempts == 0
        assert retrier.error == None
    """

    def __init__(self,
                 timeout=0,
                 backoff=None,
                 evaluator=None,
                 on_retry=None,
                 sleep_coro=None):

        # Assert input params
        assert isinstance(timeout, int), 'timeout must be an int'
        assert timeout >= 0, 'timeout cannot be a negative number'

        # Stores number of retry attempts
        self.attempts = 0
        # Stores latest error
        self.error = None
        # Maximum optional timeout in miliseconds. Use 0 for no limit
        self.timeout = timeout or 0
        # Optional evaluator function used to determine when an operation
        # should be retried or not. This allow the developer to retry
        # operations that do not raised any exception, for instance.
        # Evaluator function accepts 1 arguments: the returned task result.
        # Evaluator function can raise an exception, return an error or
        # return `True` in order to retry the operation. Otherwise the
        # operation will be considered as valid and the retry loop will end.
        self.evaluator = wraps(evaluator) if evaluator else None
        # Stores optional coroutine function to call on before very
        # retry operation. `on_retry` function accepts 2 arguments:
        # `err, next_try` and should return nothing.
        self.on_retry = wraps(on_retry) if on_retry else None
        # Backoff strategy to use. Defaults to `riprova.ConstantBackoff`.
        self.backoff = backoff or ConstantBackoff()
        # Function used to sleep. Defaults `asyncio.sleep()`.
        self.sleep = sleep_coro or asyncio.sleep

    @asyncio.coroutine
    def _call(self, coro, *args, **kw):
        """
        Calls the given coroutine function with the given variadic arguments.
        """
        res = yield from coro(*args, **kw)  # noqa (required for Python 2.x)

        # If not evaluator function response is error
        if not self.evaluator or res is None:
            # Clean error on success
            self.error = None
            # Return response object
            return res

        # Use custom result evaluator in order to determine if the
        # operation failed or not
        err = yield from self.evaluator(res)
        if not err:
            self.error = None
            return res

        # Raise custom error exception
        if isinstance(err, Exception):
            self.error = err
            raise err from RetryError

        # If True, raise a custom exception
        if err is True:
            raise RuntimeError('evaluator assertion returned True')

        # Otherwise simply return the error object
        return err

    @asyncio.coroutine
    def _handle_error(self, err):
        """
        Handle execution error state and sleep the required amount of time.
        """
        # Update latest cached error
        self.error = err

        # Get delay before next retry
        delay = self.backoff.next()

        # If backoff is ready
        if delay == Backoff.STOP:
            raise MaxRetriesExceeded('max retries exceeded') from err

        # Notify retry subscriber, if needed
        if self.on_retry:
            yield from self.on_retry(err, delay)

        # Sleep before next try
        yield from self.sleep(delay / 1000)

    @asyncio.coroutine
    def _run(self, coro, *args, **kw):
        """
        Runs coroutine in a error-safe infinitive loop until the
        operation succeed or the max retry attempts is reached.
        """
        while True:
            try:
                return (yield from self._call(coro, *args, **kw))
            except Exception as err:
                yield from self._handle_error(err)

            # Increment number of attempts
            self.attempts += 1

    @asyncio.coroutine
    def run(self, coro, *args, **kw):
        """
        Runs the given coroutine function in a retry loop until the operation
        is completed successfully or maximum retries attemps are reached.

        Arguments:
            coro (coroutinefunction): coroutine function to retry.
            *args (args): partial arguments to pass to the function.
            *kw (kwargs): partial keyword arguments to pass to the function.

        Raises:
            Exception: any potential exception raised by the function.
            RuntimeError: if evaluator function returns `True`.
            asyncio.TimeoutError: in case of a timeout exceed error.

        Returns:
            mixed: value returned by the original function.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('coro param must be a coroutine function')

        # Reset backoff on every new execution
        self.backoff.reset()

        # Reset state
        self.error = None
        self.attempts = 0

        # Run coroutine function in a timeout limited loop
        try:
            # If not timeout defined, run the coroutine function
            if self.timeout == 0:
                return (yield from self._run(coro, *args, **kw))

            # Otherwise run it with a time limited context
            with TimeoutLimit(self.timeout / 1000):
                return (yield from self._run(coro, *args, **kw))
        except asyncio.TimeoutError as err:
            raise err from self.error
