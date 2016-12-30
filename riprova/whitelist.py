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
        ImportError,
        SyntaxError,
        ReferenceError,
        KeyboardInterrupt,
        NotRetriableError
    ])

    def __init__(self, errors=None):
        self._whitelist = set(errors if errors else
                              ErrorWhitelist.WHITELIST.copy())

    @property
    def errors(self):
        """
        Sets a new error whitelist, replacing the existent one.

        Arguments:
            errors (list|tuple[Exception]): iterable containing errors to
                whitelist.
        """
        return self._whitelist

    @errors.setter
    def errors(self, errors):
        """
        Sets whilelist errors.

        Raises:
            TypeError: if set value is not a list or tuple
        """
        if not isinstance(errors, (list, tuple)):
            raise TypeError('errors must be a list or tuple')

        self._whitelist = set()
        for err in errors:
            if not issubclass(err, BaseException):
                raise TypeError('error must be a subclass of Exception')
            self._whitelist.add(err)

    def add(self, *errors):
        """
        Adds one or multiple error classes to the current whitelist.

        Arguments:
            *errors (Exception): variadic error classes to add.
        """
        # Cache current whitelist
        whitelist = self._whitelist.copy()
        # Delegate to attribute setter to run type validations
        self.errors = errors
        # Join whitelist with previous one
        self._whitelist = whitelist | self._whitelist

    def iswhitelisted(self, error):
        """
        Checks if a given error object is whitelisted or not.

        Returns:
            bool
        """
        return error and all([
            any(isinstance(error, err) for err in self._whitelist),
            getattr(error, '__retry__', False) is False
        ])


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
