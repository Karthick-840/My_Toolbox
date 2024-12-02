import logging
import os

class Logger:
  
    loglevel_dict = {
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
        50: logging.CRITICAL
    }

    def __init__(self, name_logger, logging_level, filename=None, filemode='a'):
        if filename is not None:
            if not os.path.isfile(filename):
                with open(filename, 'w') as file:
                    file.write("")  # Optionally write initial content
                print(f"File '{filename}' created")
            else:
                print(f"File '{filename}' already exists")
            # log to both file and std. out
            handlers = [logging.FileHandler(filename, mode=filemode), logging.StreamHandler()]
            logging.basicConfig(format='%(asctime)s | %(levelname)s |  %(module)s |%(funcName)s|Line %(lineno)d | %(message)s',
                                datefmt='%d-%b-%y %H:%M:%S',
                                handlers=handlers)
        else:
            

            logging.basicConfig(format='%(asctime)s | %(levelname)s |  %(module)s |%(funcName)s| %(levelname)s | Line %(lineno)d | %(message)s',
                                datefmt='%d-%b-%y %H:%M:%S')
        self.logger = logging.getLogger(name_logger)
        # Check whether the logging_level is a string or integer, if string, make sure it is uppercase.
        if isinstance(logging_level, str):
            logging_level = logging_level.upper()

        self.logger.setLevel(self.loglevel_dict[logging_level])