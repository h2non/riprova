# -*- coding: utf-8 -*-
import time
import pytest
from riprova import (Retrier, ConstantBackoff,
                     MaxRetriesExceeded, RetryTimeoutError)


def test_retrier_defaults():
    retrier = Retrier()
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout == 0
    assert retrier.on_retry is None
    assert retrier.evaluator is None
    assert retrier.sleep == time.sleep
    assert isinstance(retrier.backoff, ConstantBackoff)


def test_retrier_custom():
    def sleep(): pass

    def on_retry(): pass  # noqa

    def evaluator(): pass  # noqa

    backoff = ConstantBackoff()
    retrier = Retrier(timeout=1, on_retry=on_retry,
                      sleep_fn=sleep, evaluator=evaluator, backoff=backoff)
    assert retrier.error is None
    assert retrier.attempts == 0
    assert retrier.timeout == 1
    assert retrier.on_retry is on_retry
    assert retrier.evaluator is evaluator
    assert retrier.sleep == sleep
    assert retrier.backoff == backoff


def test_retrier_assestion_error():
    with pytest.raises(AssertionError):
        Retrier(timeout='foo')
    with pytest.raises(AssertionError):
        Retrier(timeout=-1)


def test_retrier_run_success(MagicMock):
    task = MagicMock()

    retrier = Retrier()
    retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 1
    task.assert_called_with(2, 4, foo='bar')

    assert retrier.attempts == 0
    assert retrier.error is None


def test_retrier_run_valid_retries(MagicMock):
    iterable = (ValueError, RuntimeError, NotImplementedError, True)
    task = MagicMock(side_effect=iterable)
    on_retry = MagicMock()

    retrier = Retrier(backoff=ConstantBackoff(interval=0), on_retry=on_retry)
    retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 4
    task.assert_called_with(2, 4, foo='bar')

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert retrier.error is None


def test_retrier_evaluator(MagicMock):
    iterable = (1, 2, 3, 4)
    task = MagicMock(side_effect=iterable)
    on_retry = MagicMock()

    def evaluator(x):
        if x < 4:
            raise ValueError('small number')
        return False

    retrier = Retrier(evaluator=evaluator, on_retry=on_retry,
                      backoff=ConstantBackoff(interval=0, retries=10))

    res = retrier.run(task, 2, 4, foo='bar')
    assert res == 4

    assert task.called
    assert task.call_count == 4
    task.assert_called_with(2, 4, foo='bar')

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert retrier.error is None


def test_retrier_error_evaluator_default(MagicMock):
    iterable = (1, 2, 3, 4)
    task = MagicMock(side_effect=iterable)
    on_retry = MagicMock()

    def evaluator(x):
        if x < 4:
            raise ValueError('small number')
        raise ImportError('pass error')

    retrier = Retrier(evaluator=evaluator, on_retry=on_retry,
                      backoff=ConstantBackoff(interval=0, retries=10))

    with pytest.raises(ImportError):
        retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 4
    task.assert_called_with(2, 4, foo='bar')

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert isinstance(retrier.error, ImportError)


def test_retrier_error_evaluator_custom(MagicMock):
    iterable = (1, 2, 3, 4)
    task = MagicMock(side_effect=iterable)
    on_retry = MagicMock()

    def evaluator(x):
        if x == 1:
            raise ValueError('small number')
        if x == 2:
            raise RuntimeError('small number')
        if x == 3:
            raise SyntaxError('small number')
        raise ImportError('pass error')

    def error_evaluator(err):
        # Returning True means retry the operation, otherwise stop
        return isinstance(err, (ValueError, RuntimeError, SyntaxError))

    retrier = Retrier(evaluator=evaluator, on_retry=on_retry,
                      error_evaluator=error_evaluator,
                      backoff=ConstantBackoff(interval=0, retries=10))

    with pytest.raises(ImportError):
        retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 4
    task.assert_called_with(2, 4, foo='bar')

    assert on_retry.called
    assert on_retry.call_count == 3

    assert retrier.attempts == 3
    assert isinstance(retrier.error, ImportError)


def test_retrier_run_max_retries_error(MagicMock):
    iterable = (ValueError, RuntimeError, NotImplementedError)
    task = MagicMock(side_effect=iterable)

    retrier = Retrier(backoff=ConstantBackoff(interval=0, retries=2))

    with pytest.raises(MaxRetriesExceeded):
        retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 3
    task.assert_called_with(2, 4, foo='bar')

    assert retrier.attempts == 2
    assert isinstance(retrier.error, NotImplementedError)


def test_retrier_run_max_timeout(MagicMock):
    iterable = (ValueError, NotImplementedError, RuntimeError, Exception)
    task = MagicMock(side_effect=iterable)

    retrier = Retrier(timeout=0.3, backoff=ConstantBackoff(interval=0.12))

    with pytest.raises(RetryTimeoutError):
        retrier.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count >= 2
    task.assert_called_with(2, 4, foo='bar')

    assert retrier.attempts in range(2, 4)
    assert isinstance(retrier.error, (NotImplementedError, RuntimeError))


def test_retrier_istimeout():
    assert Retrier().istimeout(1234) is False

    now = time.time() - 100
    assert Retrier(timeout=1).istimeout(now) is True


def test_retrier_context_manager(MagicMock):
    iterable = (ValueError, NotImplementedError, RuntimeError, SyntaxError)
    task = MagicMock(side_effect=iterable)

    retrier = Retrier(backoff=ConstantBackoff(interval=.1, retries=4))
    with pytest.raises(SyntaxError):
        with retrier as retry:
            retry.run(task, 2, 4, foo='bar')

    assert task.called
    assert task.call_count == 4
    task.assert_called_with(2, 4, foo='bar')

    assert retrier.attempts == 3
    assert isinstance(retrier.error, SyntaxError)


def test_retrier_context_manager_forward_error_message():
    with pytest.raises(RuntimeError) as excinfo:
        with Retrier():
            raise RuntimeError('Error message here.')
    assert str(excinfo.value) == 'Error message here.'
