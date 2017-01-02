# -*- coding: utf-8 -*-
import time
from six import raise_from
from .backoff import Backoff
from .errors import ErrorWhitelist
from .strategies import ConstantBackoff
from .exceptions import MaxRetriesExceeded, RetryError, RetryTimeoutError


class Retrier(object):
    """
    Implements a simple function retry mechanism with configurable backoff
    strategy and task timeout limit handler.

    Additionally, you can subcribe to `retry` attempts via `on_retry` param,
    which accepts a binary function.

    Retrier object also implements a context manager.

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
        error_evaluator (function): optional evaluator function used to
            determine when a task raised exception should be proccesed as
            legit error and therefore retried or, otherwise, treated as
            whitelist error, stoping the retry loop and re-raising the
            exception to the task consumer.
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
        sleep_fn (function): optional function used to sleep.
            Defaults `time.sleep()`.

    Attributes:
        whitelist (riprova.ErrorWhitelist): default error whitelist instance
            used to evaluate when.
        blacklist (riprova.ErrorBlacklist): default error blacklist instance
            used to evaluate when.
            Blacklist and Whitelist are mutually exclusive.
        timeout (int): stores the maximum retries attempts timeout in
            seconds. Use `0` for no limit. Defaults to `0`.
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
        error_evaluator (function): stores the used error evaluator function.
            Defaults to `self.is_whitelisted_error()`.
        on_retry (function): stores the retry notifier function.
            Defaults to `None`.

    Raises:
        AssertionError: in case of invalid input params.

    Usage::

        # Basic usage
        retrier = riprova.Retrier(
            timeout=10 * 1000,
            backoff=riprova.FibonacciBackoff(retries=5))

        def task(x):
            return x * x

        result = retrier.run(task, 4)
        assert result == 16
        assert retrier.attempts == 0
        assert retrier.error == None

        # Using the retrier
        retrier = riprova.Retrier(
            timeout=10 * 1000,
            backoff=riprova.FibonacciBackoff(retries=5))

        def task(x):
            return x * x

        result = retrier.run(task, 4)
        assert result == 16
        assert retrier.attempts == 0
        assert retrier.error == None

        # Using the context manager
        with riprova.Retrier() as retry:
            retry.run(task, 'foo', bar=1)

    """

    # Stores the default global error whitelist used for error retry evaluation
    whitelist = None

    # Blacklist is just a semantic alias to whitelist
    blacklist = None

    def __init__(self,
                 timeout=0,
                 backoff=None,
                 evaluator=None,
                 error_evaluator=None,
                 on_retry=None,
                 sleep_fn=None):

        # Assert input params
        if timeout is not None:
            assert isinstance(timeout, (float, int)), 'timeout must be number'
            assert timeout >= 0, 'timeout cannot be a negative number'

        # Stores number of retry attempts
        self.attempts = 0
        # Stores latest error
        self.error = None
        # Maximum optional timeout in miliseconds. Use 0 for no limit
        self.timeout = timeout or 0
        # Stores optional function to call on before very retry operation.
        # `on_retry` function accepts 2 arguments: `err, next_try` and
        # should return nothing.
        self.on_retry = on_retry
        # Stores optional evaluator function
        self.evaluator = evaluator
        # Stores the error evaluator function.
        self.error_evaluator = error_evaluator or self.is_whitelisted_error
        # Backoff strategy to use. Defaults to `riprova.ConstantBackoff`.
        self.backoff = backoff or ConstantBackoff()
        # Function used to sleep. Defaults `time.sleep()`.
        self.sleep = sleep_fn or time.sleep
        # Stores the default error whitelist used for error retry evaluation
        self.whitelist = (Retrier.blacklist or
                          Retrier.whitelist or
                          ErrorWhitelist())

    def is_whitelisted_error(self, err):
        return self.whitelist.isretry(err)

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
            err = RetryError('retry evaluator assertion returned True')
            return raise_from(err, self.error)

        # Otherwise simply return the error object
        return err

    def _timeout_error(self):
        # Timeout error
        timeout_err = RetryTimeoutError('max timeout exceeded while retrying '
                                        'task: {}s'.format(self.timeout))
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
        if self.timeout is None or self.timeout == 0:
            return False

        return time.time() - start > self.timeout > 0

    def _handle_error(self, err):
        """
        Handle execution error state and sleep the required amount of time.
        """
        # Update latest cached error
        self.error = err

        # Defaults to false
        retry = True

        # Evaluate if error is legit or should be retried
        if self.error_evaluator:
            retry = self.error_evaluator(err)

        # If evalutor returns an error exception, just raise it
        if retry and isinstance(retry, Exception):
            raise_from(retry, self.error)

        # If retry evaluator returns False, raise original error and
        # stop the retry cycle
        if retry is False:
            raise err

    def _notify_subscriber(self, delay):
        # Notify retry subscriber, if needed
        if self.on_retry:
            self.on_retry(self.error, delay)

    def _get_delay(self):
        # Get delay before next retry
        delay = self.backoff.next()

        # If backoff is done, raise an exception
        if delay == Backoff.STOP:
            return raise_from(MaxRetriesExceeded('max retries exceeded'),
                              self.error)

        return delay

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

        # Task initialization time for timeout tracking
        start = time.time()

        # Run operation in a infinitive loop until the task succeeded or
        # and max retry attempts are reached.
        while True:
            # Ensure we do not exceeded the max timeout
            print('>>', start, self.istimeout(start))
            if self.istimeout(start):
                return self._timeout_error()

            try:
                # Try running the potential failed operation
                return self._call(fn, *args, **kw)
            except Exception as err:
                # Handle error accordingly and re-raised whitelisted ones
                self._handle_error(err)

            # Get delay before next try based on the configured backoff
            delay = self._get_delay()

            # Notify retry event subscriber, if needed
            self._notify_subscriber(delay)

            # Increment retry attempts
            self.attempts += 1

            # Sleep before next try
            self.sleep(delay)

    def __enter__(self):
        # Reset state
        self.error = None
        self.attempts = 0
        return self

    def __exit__(self, error, trace, extra):
        # Forward error, if needed
        if error:
            raise error
