# -*- coding: utf-8 -*-
from riprova.constants import INT_ERROR, POS_ERROR


def test_constants():
    assert isinstance(INT_ERROR, str)
    assert INT_ERROR.format('foo') == 'foo param must be an int'

    assert isinstance(POS_ERROR, str)
    assert POS_ERROR.format('foo') == 'foo param must be a positive number'
