# -*- coding: utf-8 -*-
import asyncio  # noqa
from six import raise_from
from .backoff import Backoff
from .retrier import Retrier
from .errors import ErrorWhitelist
from .strategies import ConstantBackoff
from .exceptions import MaxRetriesExceeded, RetryError
from riprova.constants import PY_310



class AsyncRetrier(Retrier):
    """
    AsyncRetrier implements an asynchronous corutine based operation retrier.

    Only compatible with `asyncio` in Python 3.4+.

    AsyncRetrier implements a synchronous and asynchronous context manager.

    Arguments:
        timeout (int|float): maximum optional timeout in milliseconds.
            Use `None` for no limit. Defaults to `None`.
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
        error_evaluator (function|coroutinefunction): optional evaluator
            function used to determine when a task raised exception should
            be proccesed as legit error and therefore retried or, otherwise,
            treated as whitelist error, stopping the retry loop and re-raising
            the exception to the task consumer.
            This provides high versatility to developers in order to compose
            any exception, for instance. Evaluator is an unary
            function that accepts 1 argument: the raised exception object.
            Evaluator function can raise an exception, return an error or
            simply return `True` in order to retry the operation.
            Otherwise the operation will be considered as valid and the
            retry loop will end.
        on_retry (function): optional function to call on before very retry
            operation. `on_retry` function accepts 2 arguments: `err, next_try`
            and should return nothing.
        sleep_coro (coroutinefunction): optional coroutine function used to
            sleep. Defaults to `asyncio.sleep`.
        loop (asyncio.BaseException): Deprecated.
            Will always using `asyncio.get_event_loop()` in python 3.10 and above.

    Attributes:
        whitelist (riprova.ErrorWhitelist): default error whitelist instance
            used to evaluate when.
        blacklist (riprova.ErrorBlacklist): default error blacklist instance
            used to evaluate when.
            Blacklist and Whitelist are mutually exclusive.
        timeout (int): stores the maximum retries attempts timeout in
            seconds. Use `None` for no timeout. Defaults to `None`.
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
        error_evaluator (function|coroutinefunction): stores the used error
            evaluator function. Defaults to `self.is_whitelisted_error()`.
        on_retry (coroutinefunction): stores the retry notifier function.
            Defaults to `None`.

    Raises:
        AssertionError: in case of invalid input params.

    Usage::

        retrier = riprova.AsyncRetrier(
            timeout=10,
            backoff=riprova.FibonacciBackoff(retries=5))

        async def task(x):
            return x * x

        loop = asyncio.get_event_loop()

        result = loop.run_until_complete(retrier.run(task, 4))
        assert result == 16
        assert retrier.attempts == 0
        assert retrier.error == None

        # Using the async context manager
        async with riprova.AsyncRetrier() as retry:
            await retry.run(task, 'foo', bar=1)
    """

    # Stores the default global error whitelist used for error retry evaluation
    whitelist = None

    # Blacklist is just a semantic alias to whitelist
    blacklist = None

    def __init__(self,
                 timeout=None,
                 backoff=None,
                 evaluator=None,
                 error_evaluator=None,
                 on_retry=None,
                 sleep_coro=None,
                 loop=None):

        # Assert input params
        if timeout is not None:
            assert isinstance(timeout, (int, float)), 'timeout must be number'
            assert timeout >= 0, 'timeout cannot be a negative number'

        # Event loop to use
        self.loop = loop or asyncio.get_event_loop()
        # Stores number of retry attempts
        self.attempts = 0
        # Stores latest error
        self.error = None
        # Maximum optional timeout in milliseconds. Use 0 for no limit
        self.timeout = timeout or None
        # Stores optional evaluator function
        self.evaluator = asyncio.coroutine(evaluator) if evaluator else None
        # Stores the error evaluator function.
        self.error_evaluator = error_evaluator or self.is_whitelisted_error
        # Stores optional coroutine function to call on before very
        # retry operation. `on_retry` function accepts 2 arguments:
        # `err, next_try` and should return nothing.
        self.on_retry = asyncio.coroutine(on_retry) if on_retry else None
        # Backoff strategy to use. Defaults to `riprova.ConstantBackoff`.
        self.backoff = backoff or ConstantBackoff()
        # Function used to sleep. Defaults `asyncio.sleep()`.
        self.sleep = sleep_coro or asyncio.sleep
        # Stores the default error whitelist used for error retry evaluation
        self.whitelist = (AsyncRetrier.blacklist or
                          AsyncRetrier.whitelist or
                          ErrorWhitelist())

    async def _call(self, coro, *args, **kw):
        """
        Calls the given coroutine function with the given variadic arguments.
        """
        res = await coro(*args, **kw)  # noqa (required for Python 2.x)

        # If not evaluator function response is error
        if not self.evaluator or res is None:
            # Clean error on success
            self.error = None
            # Return response object
            return res

        # Use custom result evaluator in order to determine if the
        # operation failed or not
        err = await self.evaluator(res)
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

    async def _handle_error(self, err):
        """
        Handle execution error state and sleep the required amount of time.
        """
        # Update latest cached error
        self.error = err

        # Defaults to false
        retry = True

        # Evaluate if error is legit or should be retried
        if self.error_evaluator:
            retry = await (asyncio.coroutine(self.error_evaluator)(err))

        # If evalutor returns an error exception, just raise it
        if retry and isinstance(retry, Exception):
            raise_from(retry, self.error)

        # If retry evaluator returns False, raise original error and
        # stop the retry cycle
        if retry is False:
            raise err

        # Get delay before next retry
        delay = self.backoff.next()

        # If backoff is ready
        if delay == Backoff.STOP:
            raise MaxRetriesExceeded('max retries exceeded') from err

        # Notify retry subscriber, if needed
        if self.on_retry:
            await self.on_retry(err, delay)

        # Sleep before the next try attempt
        await self.sleep(delay)

    async def _run(self, coro, *args, **kw):
        """
        Runs coroutine in a error-safe infinitive loop until the
        operation succeed or the max retry attempts is reached.
        """
        err = None

        while True:
            try:
                return await self._call(coro, *args, **kw)

            # Collect raised errors by cancelled futures
            except asyncio.CancelledError as _err:
                err = _err

            # Handle any other exception error
            except Exception as _err:
                await self._handle_error(_err)

            # Increment number of retry attempts
            self.attempts += 1

            # Forward raised exception, if needed
            if err is not None:
                raise err

    async def run(self, coro, *args, **kw):
        """
        Runs the given coroutine function in a retry loop until the operation
        is completed successfully or maximum retries attempts are reached.

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

        # If not timeout defined, run the coroutine function
        if PY_310:
            return await asyncio.wait_for(
                self._run(coro, *args, **kw),
                self.timeout
            )
        else:
            return await asyncio.wait_for(
                self._run(coro, *args, **kw),
                self.timeout,
                loop=self.loop
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return self.__exit__(exc_type, exc_value, traceback)
