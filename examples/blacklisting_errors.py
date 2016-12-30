# -*- coding: utf-8 -*-
import riprova


# Custom error object
class MyCustomError(Exception):
    pass


# Blacklist of errors that should exclusively be retried
blacklist = riprova.ErrorBlacklist([
    RuntimeError,
    MyCustomError
])


def error_evaluator(error):
    """
    Used to determine if an error is legit and therefore
    should be retried or not.
    """
    return blacklist.isretry(error)


# In order to define a global blacklist policy that would be used
# across all retry instances, overwrite the blacklist attribute in Retrier.
# NOTE: blacklist overwrites any whitelist. They are mutually exclusive.
riprova.Retrier.blacklist = blacklist

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
        raise Exception('non blacklisted error')

    return x * 2


# Run task
try:
    mul2(2)
except Exception as err:
    print('Blacklisted error: {}'.format(err))
    print('Retry attempts: {}'.format(calls))
