# flake8: noqa
import riprova

@riprova.retry
def task():
    """Retry operation if it fails with constant backoff"""

@riprova.retry(backoff=riprova.ExponentialBackOff(factor=.5))
def task():
    """Retry operation if it fails using exponential backoff"""

@riprova.retry(timeout=10)
def task():
    """Raises a TimeoutError if the retry loop exceeds from 10 seconds"""

def on_retry(err, next_try):
    print('Operation error: {}'.format(err))
    print('Next try in: {}ms'.format(next_try))

@riprova.retry(on_retry=on_retry)
def task():
    """Subscribe via function callback to every retry attempt"""

def evaluator(response):
    # Force retry operation if not a valid response
    if response.status >= 400:
        raise RuntimeError('invalid response status')
    # Otherwise return False, meaning no retry
    return False

@riprova.retry(evaluator=evaluator)
def task():
    """Use a custom evaluator function to determine if the operation failed or not"""

@riprova.retry
async def task():
    """Asynchronous coroutines are also supported :)"""
