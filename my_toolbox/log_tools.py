import logging
import os
import json
from typing import Optional, Union, Dict, Any
from datetime import datetime


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


class ContextLogger:
    """
    Logger with contextual information (request_id, caller, session, etc.).
    
    All logs include context prefix, making it easy to trace related operations.
    """
    
    def __init__(
        self,
        name: str,
        logging_level: Union[str, int] = 'INFO',
        filename: Optional[str] = None,
        filemode: str = 'a'
    ):
        """
        Initialize context-aware logger.
        
        Args:
            name: Logger name
            logging_level: Log level
            filename: Optional file output
            filemode: File mode ('a' or 'w')
        """
        self.name = name
        self.context = {}
        self.base_logger = Logger(name, logging_level, filename, filemode)
        self.logger = self.base_logger.logger
    
    def set_context(self, **kwargs):
        """
        Set context variables that will be included in all subsequent logs.
        
        Args:
            **kwargs: Context key-value pairs (e.g., request_id="abc123", user="john")
        """
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context variables."""
        self.context.clear()
    
    def _format_message(self, message: str) -> str:
        """Format message with context prefix."""
        if not self.context:
            return message
        
        context_parts = [f"{k}:{v}" for k, v in self.context.items()]
        return f"[{' '.join(context_parts)}] {message}"
    
    def debug(self, message: str, **extra):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), extra=extra)
    
    def info(self, message: str, **extra):
        """Log info message with context."""
        self.logger.info(self._format_message(message), extra=extra)
    
    def warning(self, message: str, **extra):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), extra=extra)
    
    def error(self, message: str, **extra):
        """Log error message with context."""
        self.logger.error(self._format_message(message), extra=extra)
    
    def critical(self, message: str, **extra):
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), extra=extra)


class StructuredLogger:
    """
    Logger that outputs logs as JSON for aggregation systems.
    
    Each log entry is a complete JSON object with timestamp, level, context, and data.
    Ideal for ELK, Splunk, DataDog integration.
    """
    
    def __init__(
        self,
        name: str,
        filename: Optional[str] = None,
        filemode: str = 'a'
    ):
        """
        Initialize structured (JSON) logger.
        
        Args:
            name: Logger name
            filename: Output file for JSON logs
            filemode: File mode ('a' or 'w')
        """
        self.name = name
        self.filename = filename
        self.filemode = filemode
        self.context = {}
        
        if filename:
            self.file_handle = open(filename, filemode, encoding='utf-8')
        else:
            self.file_handle = None
    
    def set_context(self, **kwargs):
        """Set context variables for all subsequent logs."""
        self.context.update(kwargs)
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a structured log entry."""
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'logger': self.name,
            'level': level,
            'message': message,
            'context': self.context.copy() if self.context else {},
        }
        
        if data:
            entry['data'] = data
        
        return entry
    
    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry as JSON."""
        json_line = json.dumps(entry, ensure_ascii=False)
        
        if self.file_handle:
            self.file_handle.write(json_line + '\n')
            self.file_handle.flush()
        else:
            print(json_line)
    
    def debug(self, message: str, **data):
        """Log debug entry."""
        entry = self._create_log_entry('DEBUG', message, data if data else None)
        self._write_log(entry)
    
    def info(self, message: str, **data):
        """Log info entry."""
        entry = self._create_log_entry('INFO', message, data if data else None)
        self._write_log(entry)
    
    def warning(self, message: str, **data):
        """Log warning entry."""
        entry = self._create_log_entry('WARNING', message, data if data else None)
        self._write_log(entry)
    
    def error(self, message: str, **data):
        """Log error entry."""
        entry = self._create_log_entry('ERROR', message, data if data else None)
        self._write_log(entry)
    
    def critical(self, message: str, **data):
        """Log critical entry."""
        entry = self._create_log_entry('CRITICAL', message, data if data else None)
        self._write_log(entry)
    
    def close(self):
        """Close file handle if open."""
        if self.file_handle:
            self.file_handle.close()
    
    def __del__(self):
        """Ensure file is closed on cleanup."""
        self.close()


class MetricsLogger:
    """
    Specialized logger for numeric metrics (cache hit rates, API latencies, etc.).
    
    Logs metrics as structured data for monitoring and observability.
    """
    
    def __init__(
        self,
        name: str,
        filename: Optional[str] = None,
        filemode: str = 'a'
    ):
        """
        Initialize metrics logger.
        
        Args:
            name: Logger name
            filename: Output file for metrics (JSON Lines format)
            filemode: File mode ('a' or 'w')
        """
        self.name = name
        self.filename = filename
        self.filemode = filemode
        self.metrics = {}
        
        if filename:
            self.file_handle = open(filename, filemode, encoding='utf-8')
        else:
            self.file_handle = None
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = '',
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a single metric.
        
        Args:
            metric_name: Name of the metric (e.g., 'cache_hit_rate')
            value: Numeric value
            unit: Unit of measurement (e.g., 'ms', '%', 'requests/sec')
            tags: Optional tags (e.g., {'service': 'yfinance', 'ticker': 'AAPL'})
        """
        metric_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {},
        }
        
        json_line = json.dumps(metric_entry, ensure_ascii=False)
        
        if self.file_handle:
            self.file_handle.write(json_line + '\n')
            self.file_handle.flush()
        else:
            print(json_line)
    
    def record_timer(
        self,
        operation_name: str,
        duration_ms: float,
        success: bool = True,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record execution time for an operation.
        
        Args:
            operation_name: Name of operation (e.g., 'yfinance_fetch')
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            tags: Optional tags
        """
        timer_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'operation': operation_name,
            'duration_ms': duration_ms,
            'success': success,
            'tags': tags or {},
        }
        
        json_line = json.dumps(timer_entry, ensure_ascii=False)
        
        if self.file_handle:
            self.file_handle.write(json_line + '\n')
            self.file_handle.flush()
        else:
            print(json_line)
    
    def close(self):
        """Close file handle if open."""
        if self.file_handle:
            self.file_handle.close()
    
    def __del__(self):
        """Ensure file is closed on cleanup."""
        self.close()
