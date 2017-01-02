# -*- coding: utf-8 -*-
import abc
from six import with_metaclass


class Backoff(with_metaclass(abc.ABCMeta, object)):
    """
    Backoff representing the minimum implementable interface
    by backoff strategies.

    This class does not provide any logic, it's simply used for documentation
    purposes and type polymorphism.

    Backoff implementations are intended to be used in a single-thread context.
    """

    # Flag used by backoff strategies to notify when the retry max attempts
    # were reached and they should stop.
    STOP = -1

    @abc.abstractmethod
    def reset(self):
        """
        Resets the current backoff state data.

        Backoff strategies must implement this method.
        """

    @abc.abstractmethod
    def next(self):
        """
        Returns the number of seconds to wait before the next try,
        otherwise returns `Backoff.STOP`, which indicates the max number
        of retry operations were reached.

        Backoff strategies must implement this method.

        Returns:
            int: time to wait in seconds before the next try.
        """
