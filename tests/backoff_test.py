# -*- coding: utf-8 -*-
import pytest
from riprova import Backoff


class BackoffImplementor(Backoff):
    def __init__(self):
        self.called = False
        self.resetted = False

    def next(self):
        self.called = True

    def reset(self):
        self.resetted = True


def test_backoff():
    assert BackoffImplementor()
    assert isinstance(BackoffImplementor(), Backoff)

    backoff = BackoffImplementor()
    assert backoff.STOP == -1
    assert not backoff.called
    assert not backoff.resetted

    backoff.next()
    assert backoff.called

    backoff.reset()
    assert backoff.resetted


def test_backoff_implementation_error():
    class NotBackoff(Backoff):
        pass

    with pytest.raises(TypeError):
        Backoff()

    with pytest.raises(TypeError):
        NotBackoff()
