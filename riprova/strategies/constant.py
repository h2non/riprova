# -*- coding: utf-8 -*-
from ..backoff import Backoff
from ..constants import INT_ERROR, POS_ERROR


class ConstantBackoff(Backoff):
    """
    ConstantBackOff is a backoff policy that always returns the same
    backoff delay.

    The constant backoff policy can be configured with a custom
    retry interval and maximum number of retries.

    This is in contrast to an exponential backoff policy,
    which returns a delay that grows longer as you call `next()`.

    ConstantBackoff is expected to run in a single-thread context.

    Arguments:
        interval (int): wait interval before retry in milliseconds.
            Use `0` for no wait. Defaults to `100`.
        retries (int): maximum number of retries attempts.
            Use `0` for no limit. Defaults to `10`.

    Raises:
        AssertionError: in case of invalid params.

    Usge::

        @riprova.retry(backoff=riprova.ConstantBackoff(retries=5))
        def task(x):
            return x * x
    """

    def __init__(self, interval=100, retries=10):
        assert isinstance(retries, int), INT_ERROR.format('retries')
        assert isinstance(interval, int), INT_ERROR.format('interval')
        assert retries >= 0, POS_ERROR.format('retries')
        assert interval >= 0, POS_ERROR.format('interval')

        self.retries = retries
        self.pending_retries = retries
        self.interval = interval

    def reset(self):
        """
        Resets the current backoff state data.
        """
        self.pending_retries = self.retries

    def next(self):
        """
        Returns the number of milliseconds to wait before the next try,
        otherwise returns `Backoff.STOP`, which indicates the max number
        of retry operations were reached.

        Returns:
            int: time to wait in milliseconds before the next try.
        """
        # Verify we do not exceeded the max retries
        if self.retries > 0 and self.pending_retries == 0:
            return Backoff.STOP

        # Decrement pending retries attempts
        if self.retries > 0:
            self.pending_retries -= 1

        # Return pending interval
        return self.interval
