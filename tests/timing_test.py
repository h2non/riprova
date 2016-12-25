# -*- coding: utf-8 -*-
import time
from riprova.timing import now


def test_now():
    assert isinstance(now(), int)
    assert now() >= int(time.time() * 1000)
