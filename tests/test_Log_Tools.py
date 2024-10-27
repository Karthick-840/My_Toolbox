import os
import pytest
import logging
from My_Toolbox.Log_Tools import Logger  # Replace 'your_module' with the actual module name

@pytest.fixture
def cleanup_log_file():
    # Fixture to remove the log file after tests
    log_file = 'test_log.log'
    yield log_file
    if os.path.isfile(log_file):
        os.remove(log_file)

def test_logger_creates_file(cleanup_log_file, caplog):
    # Test logger creates a log file
    logger = Logger(name_logger='test_logger', logging_level='DEBUG', filename=cleanup_log_file)

    assert os.path.isfile(cleanup_log_file)  # Check if the file is created
    logger.logger.debug("This is a debug message")
    
    # Verify that the log message is captured
    assert "This is a debug message" in caplog.text

def test_logger_overwrites_file(cleanup_log_file, caplog):
    # Test that the logger can overwrite an existing file
    with open(cleanup_log_file, 'w') as f:
        f.write("Existing log content")

    logger = Logger(name_logger='test_logger', logging_level='DEBUG', filename=cleanup_log_file)
    
    assert os.path.isfile(cleanup_log_file)  # Check if the file still exists
    logger.logger.info("This is an info message")
    
    # Verify that the log message is captured
    assert "This is an info message" in caplog.text

def test_logger_stdout_logging(caplog):
    # Test logging to stdout
    logger = Logger(name_logger='test_logger', logging_level='INFO')

    logger.logger.warning("This is a warning message")

    # Check if the warning message is captured in the logs
    assert "This is a warning message" in caplog.text

def test_logger_invalid_log_level(cleanup_log_file):
    # Test that an invalid log level raises a KeyError
    with pytest.raises(KeyError):
        Logger(name_logger='test_logger', logging_level='INVALID_LEVEL', filename=cleanup_log_file)

def test_logger_without_file(caplog):
    # Test logger functionality without a log file
    logger = Logger(name_logger='test_logger', logging_level='DEBUG')

    logger.logger.error("This is an error message")

    # Check if the error message is captured in the logs
    assert "This is an error message" in caplog.text
