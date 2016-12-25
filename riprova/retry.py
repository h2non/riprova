# -*- coding: utf-8 -*-
import inspect
import functools
from .constants import PY_34
from .retrier import Retrier

if PY_34:  # pragma: no cover
    import asyncio
    from paco import partial
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


def retry(timeout=0, backoff=None, evaluator=None, on_retry=None, **kw):
    """
    Creates a function that accepts one or more arguments of a function and
    either invokes func returning its result if at least arity number of
    arguments have been provided, or returns a function that accepts the
    remaining function arguments until the function arity is satisfied.

    This function is overloaded: you can pass a function or coroutine function
    as first argument or an `int` indicating the explicit function arity.

    You can optionally ignore keyword based arguments as well passsing the
    `ignore_kwargs` param with `True` value.

    This function can be used as decorator.

    Arguments:
        timeout (int): optional maximum timeout in milliseconds.
            Use `0` for no limit. Defaults to `0`.
        backoff (riprova.Backoff): optional backoff strategy to use.
            Defaults to `riprova.ConstantBackoff`.
        evaluator (function|coroutinefunction): optional retry error evaluator
            function used to determine if an operator failed or not.
            Useful when domain-specific evaluation, such as valid HTTP
            responses.
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
    """
    def wrapper(fn, decorated=True):
        if not iscallable(fn):
            raise TypeError('first argument must a coroutine function, a '
                            'function or a method.')

        # Resolve the required retrier instance
        RetrierClass = (AsyncRetrier
                        if asyncio and asyncio.iscoroutinefunction(fn)
                        else Retrier)

        # Normalize potentially overloaded timeout param
        _timeout = timeout if decorated else 0

        # Otherwise return recursive currier function
        retrier = RetrierClass(backoff=backoff, timeout=_timeout,
                               evaluator=evaluator, on_retry=on_retry, **kw)

        # Return partial function application
        return (partial(retrier.run, fn)
                if AsyncRetrier and isinstance(retrier, AsyncRetrier)
                else functools.partial(retrier.run, fn))

    # Return currier function or decorator wrapper
    return wrapper(timeout, False) if iscallable(timeout) else wrapper
