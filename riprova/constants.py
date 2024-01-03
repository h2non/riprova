# -*- coding: utf-8 -*-
import sys

# Store if Python runtime is higher or equal to 3.4
PY_34 = sys.version_info >= (3, 4)
PY_35 = sys.version_info >= (3, 5)
PY_310 = sys.version_info >= (3, 10)

# Assertion template errors
INT_ERROR = '{} param must be an int'
POS_ERROR = '{} param must be a positive number'
