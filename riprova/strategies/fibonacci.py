# -*- coding: utf-8 -*-
from ..backoff import Backoff
from ..constants import INT_ERROR, POS_ERROR


class FibonacciBackoff(Backoff):
    """
    Implements a backoff policy based on Fibonacci sequence of numbers.

    The Fibonacci backoff policy can be configured with a custom
    initial sequence number value and maximum number of retries.

    This policy is similar to exponential backoff policy,
    which returns a delay that grows longer as you call `next()`.

    For more information, see:
    https://en.wikipedia.org/wiki/Fibonacci_number

    FibonacciBackoff is expected to run in a single-thread context.

    Arguments:
        retries (int): maximum number of retries.
            Use `0` for no limit. Defaults to `10`.
        initial (int): initial number for fibonacci serie.
            Detaults to `1`.
        multiper (int): fibonacci serie number time multiplier.
            Defaults to `1`.

    Raises:
        AssertionError: in case of invalid params.

    Usage::

        @riprova.retry(backoff=riprova.FibonacciBackoff(retries=5))
        def task(x):
            return x * x
    """

    def __init__(self, retries=10, initial=1, multiplier=1):
        # Validate input params
        assert isinstance(retries, int), INT_ERROR.format('retries')
        assert isinstance(initial, int), INT_ERROR.format('initial')
        assert isinstance(multiplier, int), INT_ERROR.format('multiplier')
        assert retries >= 0, POS_ERROR.format('retries')
        assert initial >= 0, POS_ERROR.format('initial')
        assert multiplier >= 0, POS_ERROR.format('multiplier')

        self.prev = 0
        self.retries = 0
        self.current = initial or 1
        self.initial = self.current
        self.max_retries = retries
        self.multiplier = multiplier

    @property
    def interval(self):
        """
        Returns the next Fibonacci number in the serie, multiplied by
        the current configured multiplier, typically `100`, for time
        seconds adjust.
        """
        current = self.prev + self.current
        self.prev = self.current
        self.current = current
        return self.current * self.multiplier

    def reset(self):
        """
        Resets the current backoff state data.
        """
        self.prev = 0
        self.retries = 0
        self.current = self.initial

    def next(self):
        """
        Returns the number of seconds to wait before the next try,
        otherwise returns `Backoff.STOP`, which indicates the max number
        of retry operations were reached.

        Returns:
            float: time to wait in seconds before the next try.
        """
        # Verify we do not exceeded the max retries
        if self.max_retries > 0 and self.retries >= self.max_retries:
            return Backoff.STOP

        # Decrement pending retries attempts
        if self.max_retries > 0:
            self.retries += 1

        # Return next interval according to Fibonacci serie
        return self.interval
