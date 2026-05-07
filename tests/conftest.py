import pathlib
import sys
import logging

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)
        return None

    def error(self, message):
        self.messages.append(message)
        return None

    def getChild(self, _name):
        return self


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def dummy_logger():
    return DummyLogger()


@pytest.fixture
def std_logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    return logger
