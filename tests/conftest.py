import pytest


@pytest.fixture(scope='session', autouse=True)
def MagicMock():
    try:
        from unittest.mock import MagicMock
    except Exception as error:
        from mock import MagicMock
    return MagicMock
