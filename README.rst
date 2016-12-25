riprova |Build Status| |PyPI| |Coverage Status| |Documentation Status| |Stability| |Quality| |Versions|
=======================================================================================================

Small, generic and versatile `Python`_ library providing retry mechanisms with multiple backoff strategies for failed operations.

For an brief introduction about backoff mechanisms for potential failed operations, `read this article`_.


Features
--------

-  Retry decorator for simple and idiomatic consumption.
-  Maximum retry timeout support.
-  Automatically retry operations on raised exceptions.
-  Configurable maximum number of retry attempts.
-  Custom retry evaluator function, useful to determine when an operation failed or not.
-  Highly configurable supporting max retries, timeouts or retry notifier callback.
-  Built-in back-off strategies: constant, `fibonacci`_ and `exponential`_ back-offs.
-  Pluggable, custom back-off strategies.
-  Supports asynchronous coroutines with `async/await` and `yield from` syntax.
-  Lightweight small library with zero embedding cost.
-  Works with Python +2.6, 3.0+ and PyPy.


Backoff strategies
------------------

List of built-in backoff strategies.

- `Constant backoff`_
- `Fibonacci backoff`_
- `Exponential backoff`_

You can also implement your own one easily.
See `ConstantBackoff`_ for an implementation reference.


Installation
------------

Using ``pip`` package manager (requires pip 1.8+. Upgrade it running: ``pip install -U pip``):

.. code-block:: bash

    pip install -U riprova

Or install the latest sources from Github:

.. code-block:: bash

    pip install -e git+git://github.com/h2non/riprova.git#egg=riprova


API
---

- riprova.retry_
- riprova.Retrier_
- riprova.AsyncRetrier_
- riprova.Backoff_
- riprova.ConstantBackoff_
- riprova.FibonacciBackoff_
- riprova.ExponentialBackoff_
- riprova.RetryError_
- riprova.RetryTimeoutError_
- riprova.MaxRetriesExceeded_


.. _riprova.retry: http://riprova.readthedocs.io/en/latest/api.html#riprova.retry
.. _riprova.Retrier: http://riprova.readthedocs.io/en/latest/api.html#riprova.Retrier
.. _riprova.AsyncRetrier: http://riprova.readthedocs.io/en/latest/api.html#riprova.AsyncRetrier
.. _riprova.Backoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.Backoff
.. _riprova.ConstantBackoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.ConstantBackoff
.. _riprova.FibonacciBackoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.FibonacciBackoff
.. _riprova.ExponentialBackoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.ExponentialBackoff
.. _riprova.RetryError: http://riprova.readthedocs.io/en/latest/api.html#riprova.RetryError
.. _riprova.RetryTimeoutError: http://riprova.readthedocs.io/en/latest/api.html#riprova.RetryTimeoutError
.. _riprova.MaxRetriesExceeded: http://riprova.readthedocs.io/en/latest/api.html#riprova.MaxRetriesExceeded


Examples
^^^^^^^^

You can see all the featured examples from the `documentation`.

**Basic usage examples**:

.. code-block:: python

    import riprova

    @riprova.retry
    def task():
        """Retry operation if it fails with constant backoff"""

    @riprova.retry(backoff=riprova.ExponentialBackOff(factor=0.5))
    def task():
        """Retry operation if it fails using exponential backoff"""

    @riprova.retry(timeout=10000)
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


**Retry failed HTTP requests**:

.. code-block:: python

    import pook
    import requests
    from riprova import retry

    # Define HTTP mocks
    pook.get('server.com').times(3).reply(503)
    pook.get('server.com').times(1).reply(200).json({'hello': 'world'})


    # Retry evaluator function used to determine if the operated failed or not
    def evaluator(response):
        if response != 200:
            return Exception('failed request')
        return False


    # On retry even subscriptor
    def on_retry(err, next_try):
        print('Operation error {}'.format(err))
        print('Next try in {}ms'.format(next_try))


    # Register retriable operation
    @retry(evaluator=evaluator, on_retry=on_retry)
    def fetch(url):
        return requests.get(url)


    # Run request
    fetch('http://server.com')



License
-------

MIT - Tomas Aparicio

.. _exponential: https://en.wikipedia.org/wiki/Exponential_backoff
.. _fibonacci: https://en.wikipedia.org/wiki/Fibonacci_number
.. _asyncio: https://docs.python.org/3.5/library/asyncio.html
.. _Python: http://python.org
.. _annotated API reference: https://h2non.github.io/paco
.. _async/await: https://www.python.org/dev/peps/pep-0492/
.. _yield from: https://www.python.org/dev/peps/pep-0380/
.. _documentation: http://riprova.readthedocs.io/en/latest/examples.html
.. _read this article: http://dthain.blogspot.ie/2009/02/exponential-backoff-in-distributed.html
.. _Constant backoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.ConstantBackoff
.. _Fibonacci backoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.FibonacciBackoff
.. _Exponential backoff: http://riprova.readthedocs.io/en/latest/api.html#riprova.ExponentialBackOff
.. _ConstantBackoff: https://github.com/h2non/riprova/blob/master/riprova/strategies/constant.py


.. |Build Status| image:: https://travis-ci.org/h2non/riprova.svg?branch=master
   :target: https://travis-ci.org/h2non/riprova
.. |PyPI| image:: https://img.shields.io/pypi/v/riprova.svg?maxAge=2592000?style=flat-square
   :target: https://pypi.python.org/pypi/riprova
.. |Coverage Status| image:: https://coveralls.io/repos/github/h2non/riprova/badge.svg?branch=master
   :target: https://coveralls.io/github/h2non/riprova?branch=master
.. |Documentation Status| image:: https://img.shields.io/badge/docs-latest-green.svg?style=flat
   :target: http://riprova.readthedocs.io/en/latest/?badge=latest
.. |Quality| image:: https://codeclimate.com/github/h2non/riprova/badges/gpa.svg
   :target: https://codeclimate.com/github/h2non/riprova
.. |Stability| image:: https://img.shields.io/pypi/status/riprova.svg
   :target: https://pypi.python.org/pypi/riprova
.. |Versions| image:: https://img.shields.io/pypi/pyversions/riprova.svg
   :target: https://pypi.python.org/pypi/riprova
