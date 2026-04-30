import logging
import os
from typing import Optional, Union, Dict


class Logger:
    """Logger class for creating and configuring Python loggers."""

    loglevel_dict: Dict[Union[str, int], int] = {
        'NOTSET': logging.NOTSET,
        0: logging.NOTSET,
        'DEBUG': logging.DEBUG,
        10: logging.DEBUG,
        'INFO': logging.INFO,
        20: logging.INFO,
        'WARNING': logging.WARNING,
        30: logging.WARNING,
        'ERROR': logging.ERROR,
        40: logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        50: logging.CRITICAL,
        'UPDATE': logging.CRITICAL,
    }

    def __init__(self, name_logger: str, logging_level: Union[str, int],
                 filename: Optional[str] = None, filemode: str = 'a'):
        """Initialize a logger with console and optional file output.

        Args:
            name_logger: Name of the logger
            logging_level: Logging level (string like 'INFO' or integer like 20)
            filename: Optional file path for log output
            filemode: File mode for log file ('a' for append, 'w' for write)
        """
        if filename is not None:
            if not os.path.isfile(filename):
                with open(filename, 'w') as file:
                    file.write("")
                print(f"File '{filename}' created")
            else:
                print(f"File '{filename}' already exists")
            # log to both file and stdout
            handlers = [logging.FileHandler(filename, mode=filemode), logging.StreamHandler()]
            logging.basicConfig(
                format='%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | Line %(lineno)d | %(message)s',
                datefmt='%d-%b-%y %H:%M:%S',
                handlers=handlers
            )
        else:
            logging.basicConfig(
                format='%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | Line %(lineno)d | %(message)s',
                datefmt='%d-%b-%y %H:%M:%S'
            )
        self.logger = logging.getLogger(name_logger)
        # Check whether the logging_level is a string or integer; if string, uppercase it.
        if isinstance(logging_level, str):
            logging_level = logging_level.upper()

        self.logger.setLevel(self.loglevel_dict[logging_level])