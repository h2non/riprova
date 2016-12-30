# -*- coding: utf-8 -*-
import riprova


# Custom error object
class MyCustomError(Exception):
    pass


# Whitelist of errors that should not be retried
whitelist = riprova.ErrorWhitelist([
    ReferenceError,
    ImportError,
    IOError,
    SyntaxError,
    IndexError
])


def error_evaluator(error):
    """
    Used to determine if an error is legit and therefore
    should be retried or not.
    """
    return whitelist.isretry(error)


# In order to define a global whitelist policy that would be used
# across all retry instances, overwrite the whitelist attribute in Retrier:
riprova.Retrier.whitelist = whitelist

# Store number of function calls for error simulation
calls = 0


# Register retriable operation with a custom error evaluator
# You should pass the evaluator per retry instance.
@riprova.retry(error_evaluator=error_evaluator)
def mul2(x):
    global calls

    if calls < 3:
        calls += 1
        raise RuntimeError('simulated call error')

    if calls == 3:
        calls += 1
        raise ReferenceError('legit error')

    return x * 2


# Run task
try:
    mul2(2)
except ReferenceError as err:
    print('Whitelisted error: {}'.format(err))
    print('Retry attempts: {}'.format(calls))
