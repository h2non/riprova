History
=======

v0.1.3 / 2016-12-30
-------------------

* refactor(async_retrier): simplify coroutine wrapper
* feat(whitelist): add whitelist and blacklist support
* feat(tests): add missing test cases for whitelist
* feat(retry): pass error_evaluator param
* fix(retrier): cast delay to float
* fix(tests): use valid exception for Python 2.7
* feat(#6): add custom error whilelist and custom error evaluator function
* Merge pull request #8 from tsarpaul/master
* refactor(decorator): do not expose retrier instance

v0.1.2 / 2016-12-27
-------------------

* fix(decorator): wrap retries instance per function call

v0.1.1 / 2016-12-27
-------------------

* fix(`#2`_): handle and forward ``asyncio.CancelledError`` as non-retriable error

v0.1.0 / 2016-12-25
-------------------

* First version


.. _#2: https://github.com/h2non/riprova/issues/2
