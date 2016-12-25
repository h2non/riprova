# -*- coding: utf-8 -*-
import random
from ..timing import now
from ..backoff import Backoff
from ..constants import INT_ERROR, POS_ERROR


class ExponentialBackOff(Backoff):
    """
    ExponentialBackOff is a backoff implementation that increases the backoff
    period for each retry attempt using a randomization function that grows
    exponentially.

    `next()` returned interval is calculated using the following formula:

        randomized interval = (
            interval * (random value in range [1 - factor, 1 + factor]))

    `next()` will range between the randomization factor percentage below
    and above the retry interval.

    For example, given the following parameters:

    - interval = 200
    - factor = 0.5
    - multiplier = 2

    the actual backoff period used in the next retry attempt will range
    between 1 and 3 seconds, multiplied by the exponential, that is, between
    2 and 6 seconds.

    Note: `max_internval` caps the `interval` and not the randomized interval.

    If the time elapsed since an `ExponentialBackOff` instance is created
    goes past the `max_elapsed` time, then the method `next()` starts
    returning `Backoff.STOP`.

    The elapsed time can be reset by calling `reset()``.

    Example: Given the following default arguments, for 10 tries the sequence
    will be, and assuming we go over the `max_elapsed` on the 10th try::

        Request #  RetryInterval (seconds)  Randomized Interval (seconds)
        1          0.5                     [0.25,   0.75]
        2          0.75                    [0.375,  1.125]
        3          1.125                   [0.562,  1.687]
        4          1.687                   [0.8435, 2.53]
        5          2.53                    [1.265,  3.795]
        6          3.795                   [1.897,  5.692]
        7          5.692                   [2.846,  8.538]
        8          8.538                   [4.269, 12.807]
        9          12.807                  [6.403, 19.210]
        10         19.210                  Backoff.STOP


    For the opposite backoff strategy, see `riprova.ConstantBackoff`.

    `ExponentialBackOff` is expected to run in a single-thread context.

    Arguments:
        interval (int): interval time in milliseconds.
            Defaults to `500`.
        factor (int|float): multiplier factor for exponential retries.
            Defaults to `0.5`. It should be between `0` and `1` number range.
        max_interval (int): max allowed internval in milliseconds.
            Defaults to `60`.
        max_elapsed (int): max elapsed total allowed time in milliseconds.
            Defaults to `15` minutes == `15 * 60 * 1000` milliseconds.
        multiplier (int|float): exponential multiplier.
            Defaults to `1.5`.

    Raises:
        AssertionError: in case of invalid params.

    Usage::

        @riprova.retry(backoff=riprova.ExponentialBackOff(interval=100))
        def task(x):
            return x * x
    """

    def __init__(self,
                 interval=500,
                 factor=0.5,
                 max_interval=6000,
                 max_elapsed=15 * 60 * 1000,
                 multiplier=1.5):

        # Assert valid params
        assert isinstance(interval, int), INT_ERROR.format('interval')
        assert isinstance(multiplier, (int, float)), INT_ERROR.format('multiplier')  # noqa
        assert isinstance(factor, (int, float)), INT_ERROR.format('factor')
        assert isinstance(max_elapsed, int), INT_ERROR.format('max_elapsed')
        assert isinstance(max_interval, int), INT_ERROR.format('max_interval')
        assert interval >= 0, POS_ERROR.format('interval')
        assert multiplier >= 0, POS_ERROR.format('multiplier')

        self.started = None  # start time in milliseconds
        self.multiplier = multiplier
        self.max_elapsed = max_elapsed
        self.max_interval = max_interval
        self.factor = min(max(factor, 0), 1)
        self.interval = interval
        self.current_interval = interval

    @property
    def elapsed(self):
        """
        Returns the elapsed time since an `ExponentialBackOff` instance
        is created and is reset when `reset()` is called.
        """
        return now() - self.started

    def reset(self):
        """
        Reset the interval back to the initial retry interval and
        restarts the timer.
        """
        self.started = None
        self.current_interval = self.interval

    def next(self):
        """
        Returns the number of milliseconds to wait before the next try,
        otherwise returns `Backoff.STOP`, which indicates the max number
        of retry operations were reached.

        Returns:
            int: time to wait in milliseconds before the next try.
        """
        # Store start time
        if self.started is None:
            self.started = now()

        # Make sure we have not gone over the maximum elapsed time.
        if self.max_elapsed != 0 and self.elapsed > self.max_elapsed:
            return Backoff.STOP

        # Get random exponential interval
        interval = self._get_random_value()

        # Incremental interval
        self._increment_interval()

        # Return interval
        return interval

    def _increment_interval(self):
        """
        Increments the current interval by multiplying it with the multiplier.
        """
        # Check for overflow, if overflow is detected set the current
        # interval to the max interval.
        if self.current_interval >= (self.max_interval / self.multiplier):
            self.current_interval = self.max_interval
        else:
            self.current_interval = self.current_interval * self.multiplier

    def _get_random_value(self):
        """
        Returns a random value from the following interval:

            [factor * current_interval, factor * current_interval]

        Returns:
            int: interval milliseconds to wait before next try.
        """
        rand = random.random()
        delta = self.factor * rand

        min_interval = self.current_interval - delta
        max_interval = self.current_interval + delta

        # Get a random value from the range [min_interval, max_interval].
        # The formula used below has a +1 because if the min_interval is 1 and
        # the max_interval is 3 then we want a 33% chance for selecting either
        # 1, 2 or 3.
        return int(min_interval + (rand * (max_interval - min_interval + 1)))
