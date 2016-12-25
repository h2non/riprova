# -*- coding: utf-8 -*-
import riprova

# Store number of function calls for error simulation
calls = 0


# Register retriable operation with custom evaluator
@riprova.retry
def mul2(x):
    global calls

    if calls < 3:
        calls += 1
        raise RuntimeError('simulated call error')

    return x * 2


# Run task
result = mul2(2)
print('Result:', result)
