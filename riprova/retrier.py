# -*- coding: utf-8 -*-
import time
from six import raise_from
from .timing import now
from .backoff import Backoff
from .strategies import ConstantBackoff
from .exceptions import MaxRetriesExceeded, RetryError, RetryTimeoutError


class Retrier(object):
    """
    Implements a simple function retry mechanism.

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
        sleep_fn (function): optional function used to sleep.
            Defaults `time.sleep()`.

    Attributes:
        timeout (int): stores the maximum retries attempts timeout in
            milliseconds. Use `0` for no limit. Defaults to `0`.
        attempts (int): number of retry attempts being executed from last
            `run()` method call.
        error (Exception): stores the latest generated error.
            `None` if not error yet from last `run()` execution.
        sleep (function): stores the function used to sleep.
            Defaults to `time.sleep`.
        backoff (Backoff): stores current used backoff.
            Defaults to `riprova.ConstantBackoff`.
        evaluator (function): stores the used evaluator function.
            Defaults to `None`.
        on_retry (function): stores the retry notifier function.
            Defaults to `None`.

    Raises:
        AssertionError: in case of invalid input params.

    Usage::

        retrier = riprova.Retrier(
            timeout=10 * 1000,
            backoff=riprova.FibonacciBackoff(retries=5))

        def task(x):
            return x * x

        result = retrier.run(task, 4)
        assert result == 16
        assert retrier.attempts == 0
        assert retrier.error == None

    """

    def __init__(self,
                 timeout=0,
                 backoff=None,
                 evaluator=None,
                 on_retry=None,
                 sleep_fn=None):

        # Assert input params
        assert isinstance(timeout, int), 'timeout must be an int'
        assert timeout >= 0, 'timeout cannot be a negative number'

        # Stores number of retry attempts
        self.attempts = 0
        # Stores latest error
        self.error = None
        # Maximum optional timeout in miliseconds. Use 0 for no limit
        self.timeout = timeout
        # Stores optional function to call on before very retry operation.
        # `on_retry` function accepts 2 arguments: `err, next_try` and
        # should return nothing.
        self.on_retry = on_retry
        # Optional evaluator function used to determine when an operation
        # should be retried or not. This allow the developer to retry
        # operations that do not raised any exception, for instance.
        # Evaluator function accepts 1 arguments: the returned task result.
        # Evaluator function can raise an exception, return an error or
        # return `True` in order to retry the operation. Otherwise the
        # operation will be considered as valid and the retry loop will end.
        self.evaluator = evaluator
        # Backoff strategy to use. Defaults to `riprova.ConstantBackoff`.
        self.backoff = backoff or ConstantBackoff()
        # Function used to sleep. Defaults `time.sleep()`.
        self.sleep = sleep_fn or time.sleep

    def _call(self, fn, *args, **kw):
        """
        Calls the given function with the given variadic arguments
        """
        # Call original function with input arguments
        res = fn(*args, **kw)
        if not self.evaluator or res is None:
            # Clean error on success
            self.error = None
            # Return response object
            return res

        # Use custom result evaluator in order to determine if the
        # operation failed or not
        err = self.evaluator(res)
        if not err:
            self.error = None
            return res

        # Raise custom error exception
        if isinstance(err, Exception):
            self.error = err
            return raise_from(err, RetryError('retry loop error'))

        # If True, raise a custom exception
        if err is True:
            err = RetryError('evaluator assertion returned True')
            return raise_from(err, self.error)

        # Otherwise simply return the error object
        return err

    def _timeout_error(self):
        timeout_err = RetryTimeoutError('max timeout exceeded while retrying '
                                        'task: {}ms'.format(self.timeout))
        # Raise timeout error
        raise_from(timeout_err, self.error)

    def istimeout(self, start):
        """
        Verifies if the current timeout.

        Arguments:
            start (int): start UNIX time in miliseconds.

        Returns:
            bool: `True` if timeout exceeded, otherwise `False`.
        """
        return self.timeout > 0 and (now() - start) > self.timeout

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
            return raise_from(MaxRetriesExceeded('max retries exceeded'), err)

        # Notify retry subscriber, if needed
        if self.on_retry:
            self.on_retry(err, delay)

        # Sleep before next try
        self.sleep(0.5)

    def run(self, fn, *args, **kw):
        """
        Runs the given function in a retry loop until the operation is
        completed successfully or maximum retries attemps are reached.

        Arguments:
            fn (function): operation to retry.
            *args (args): partial arguments to pass to the function.
            *kw (kwargs): partial keyword arguments to pass to the function.

        Raises:
            Exception: any potential exception raised by the function.
            RetryTimeoutError: in case of a timeout exceed.
            RuntimeError: if evaluator function returns `True`.

        Returns:
            mixed: value returned by the original function.
        """
        # Reset state
        self.error = None
        self.attempts = 0

        # Reset backoff strategy on every new run. Backoff are supposed to be
        # used in single thread environment.
        self.backoff.reset()

        # Store task initialization time for timeouts
        start = now()

        # Run operation in a infinitive loop until the task succeeded or
        # and max retry attemts are reached.
        while True:
            # Ensure we do not exceeded the max timeout
            if self.istimeout(start):
                return self._timeout_error()

            try:
                # Try running the potential failed operation
                return self._call(fn, *args, **kw)
            except Exception as err:
                self._handle_error(err)

            # Increment retry attempts
            self.attempts += 1
