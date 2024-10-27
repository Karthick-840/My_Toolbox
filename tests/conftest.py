# conftest.py

import logging
import pytest

@pytest.fixture
def logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    return logger
