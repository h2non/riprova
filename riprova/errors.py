# -*- coding: utf-8 -*-
from .exceptions import NotRetriableError


class ErrorWhitelist(object):
    """
    Stores an error whitelist and provides a simple interface for whitelist
    update and mutation.

    Arguments:
        errors (set|list|tuple[Exception]): optional list of error exceptions
            classes to whitelist.

    Attributes:
        errors (list): list of whilelist errors.
    """

    # Whitelist built-in exceptions that would be ignored by the retrier
    # engine. User can mutate and extend this list via class method.
    WHITELIST = set([
        SystemExit,
        IndexError,
        ImportError,
        SyntaxError,
        ReferenceError,
        KeyboardInterrupt,
        NotRetriableError
    ])

    def __init__(self, errors=None):
        self._list = set(errors if errors else ErrorWhitelist.WHITELIST.copy())

    @property
    def errors(self):
        """
        Sets a new error whitelist, replacing the existent one.

        Arguments:
            errors (list|tuple[Exception]): iterable containing errors to
                whitelist.
        """
        return self._list

    @errors.setter
    def errors(self, errors):
        """
        Sets whilelist errors.

        Raises:
            TypeError: if set value is not a list or tuple
        """
        if not isinstance(errors, (list, tuple)):
            raise TypeError('errors must be a list or tuple')

        self._list = set()
        for err in errors:
            if not issubclass(err, BaseException):
                raise TypeError('error must be a subclass of Exception')
            self._list.add(err)

    def add(self, *errors):
        """
        Adds one or multiple error classes to the current whitelist.

        Arguments:
            *errors (Exception): variadic error classes to add.
        """
        # Cache current whitelist
        whitelist = self._list.copy()
        # Delegate to attribute setter to run type validations
        self.errors = errors
        # Join whitelist with previous one
        self._list = whitelist | self._list

    def isretry(self, error):
        """
        Checks if a given error object is whitelisted or not.

        Returns:
            bool
        """
        return not all([
            error is not None,
            any(isinstance(error, err) for err in self._list),
            getattr(error, '__retry__', False) is False
        ])


class ErrorBlacklist(ErrorWhitelist):
    """
    Provides errors blacklist used to determine those exception errors who
    should be retried.

    Implements the opposite behaviour to `ErrorWhitelist`.

    Arguments:
        errors (set|list|tuple[Exception]): optional list of error exceptions
            classes to blacklist.

    Attributes:
        errors (list): list of blacklist errors.
    """

    def isretry(self, error):
        """
        Checks if a given error object is not whitelisted.

        Returns:
            bool
        """
        return not ErrorWhitelist.isretry(self, error)


def add_whitelist_error(*errors):
    """
    Add additional custom errors to the global whitelist.

    Raises exceptions that are instances of the whitelisted errors won't be
    retried and they will be re-raised instead.

    Arguments:
        *errors (Exception): variadic error classes to whitelist.

    Usage::

        riprova.add_whitelist_error(MyCustomError, AnotherError)
    """
    [ErrorWhitelist.WHITELIST.add(error)
     for error in errors
     if issubclass(error, BaseException)]
