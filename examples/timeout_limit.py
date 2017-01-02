# -*- coding: utf-8 -*-
import riprova

# Store number of function calls for error simulation
calls = 0


# Register retriable operation with custom evaluator
@riprova.retry(timeout=0.3)
def mul2(x):
    global calls

    if calls < 4:
        calls += 1
        raise RuntimeError('simulated call error')

    return x * 2


# Run task
try:
    mul2(2)
except riprova.RetryTimeoutError as err:
    print('Timeout error: {}'.format(err))
