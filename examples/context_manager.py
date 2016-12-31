# -*- coding: utf-8 -*-
import riprova

# Store number of function calls for error simulation
calls = 0


# Register retriable operation with custom evaluator
def mul2(x):
    global calls

    if calls < 4:
        calls += 1
        raise RuntimeError('simulated call error')

    return x * 2


# Run task via context manager
with riprova.Retrier() as retry:
    result = retry.run(mul2, 2)
    print('Result 1: {}'.format(result))


# Or alternatively create a shared retrier and reuse it across multiple
# context managers.
retrier = riprova.Retrier()

with retrier as retry:
    calls = 0
    result = retry.run(mul2, 4)
    print('Result 2: {}'.format(result))

with retrier as retry:
    calls = 0
    result = retry.run(mul2, 8)
    print('Result 3: {}'.format(result))
