# -*- coding: utf-8 -*-
import inspect
import functools
from .constants import PY_34
from .retrier import Retrier

if PY_34:  # pragma: no cover
    import asyncio
    from .async_retrier import AsyncRetrier
else:
    asyncio, AsyncRetrier, partial = None, None, None


def iscallable(x):
    """
    Returns `True` if the given value is a callable object.
    """
    return any([
        inspect.isfunction(x),
        inspect.ismethod(x),
        asyncio and asyncio.iscoroutinefunction(x)
    ])


def retry(timeout=0, backoff=None, evaluator=None,
          error_evaluator=None, on_retry=None, **kw):
    """
    Decorator function that wraps function, method or coroutine function that
    would be retried on failure capabilities.

    Retry policy can be configured via `backoff` param.

    You can also use a custom evaluator function used to determine when the
    returned task value is valid or not, retrying the operation accordingly.

    You can subscribe to every retry attempt via `on_retry` param, which
    accepts a function or a coroutine function.

    This function is overloaded: you can pass a function or coroutine function
    as first argument or an `int` indicating the `timeout` param.

    This function as decorator.

    Arguments:
        timeout (int): optional maximum timeout in milliseconds.
            Use `0` for no limit. Defaults to `0`.
        backoff (riprova.Backoff): optional backoff strategy to use.
            Defaults to `riprova.ConstantBackoff`.
        evaluator (function|coroutinefunction): optional retry result evaluator
            function used to determine if an operator failed or not.
            Useful when domain-specific evaluation, such as valid HTTP
            responses.
        error_evaluator (function|coroutinefunction): optional error
            evaluator function usef to determine if a reased exception is
            legit or not, and therefore should be handled as a failure or
            simply forward the raised exception and stop the retry cycle.
            This is useful in order to ignore custom error exceptions.
        on_retry (function|coroutinefunction): optional on retry event
            subscriber that will be executed before every retry attempt.
            Useful for reporting and tracing.
        sleep_fn (function|coroutinefunction): optional sleep function to be
            used before retry attempts.
            Defaults to `time.sleep()` or `asyncio.sleep()`.
        *kwargs (mixed): keyword variadic arguments to pass to `Retrier`
            class constructor.

    Raises:
        TypeError: if function is not a function or coroutine function.

    Returns:
        function or coroutinefunction: decorated function or coroutine
            function with retry mechanism.

    Usage::

        @riprova.retry
        def task(x, y):
            return x * y

        task(4, 4)
        # => 16

        @riprova.retry(backoff=riprova.FinonacciBackoff(retries=10))
        def task(x, y):
            return x * y

        task(4, 4)
        # => 16

        @riprova.retry(timeout=10)
        async def task(x, y):
            return x * y

        await task(4, 4)
        # => 16

        def on_retry(err, next_try):
            print('Error exception: {}'.format(err))
            print('Next try in {}ms'.format(next_try))

        @riprova.retry(on_retry=on_retry)
        async def task(x, y):
            return x * y

        await task(4, 4)
        # => 16
    """
    def decorator(fn, decorated=True):
        if not iscallable(fn):
            raise TypeError('first argument must a coroutine function, a '
                            'function or a method.')

        # Resolve the required retrier instance
        RetrierClass = (AsyncRetrier
                        if asyncio and asyncio.iscoroutinefunction(fn)
                        else Retrier)

        # Normalize potentially overloaded timeout param
        _timeout = timeout if decorated else 0

        @functools.wraps(fn)
        def wrapper(*args, **kw):
            # Otherwise return recursive currier function
            retrier = RetrierClass(backoff=backoff,
                                   timeout=_timeout,
                                   evaluator=evaluator,
                                   error_evaluator=error_evaluator,
                                   on_retry=on_retry, **kw)

            # Return partial function application
            retry_runner = functools.partial(retrier.run, fn)

            # Run original function via retry safe runner
            return retry_runner(*args, **kw)

        # Return retry wrapper function
        return wrapper

    # Return retry delegator or decorator wrapper
    return decorator(timeout, False) if iscallable(timeout) else decorator
