# -*- coding: utf-8 -*-
import time


def now():
    """
    Returns the current system date.

    Returns:
        int: current system date in miliseconds
    """
    return int(time.time() * 1000)
