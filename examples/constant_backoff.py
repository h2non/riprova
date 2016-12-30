# -*- coding: utf-8 -*-
import riprova

# Store number of function calls for error simulation
calls = 0

# Max number of retries attempts
retries = 5


# Register retriable operation with custom evaluator
@riprova.retry(backoff=riprova.ConstantBackoff(interval=500, retries=retries))
def mul2(x):
    global calls

    if calls < 4:
        calls += 1
        raise RuntimeError('simulated call error')

    return x * 2


# Run task
result = mul2(2)
print('Result: {}'.format(result))
