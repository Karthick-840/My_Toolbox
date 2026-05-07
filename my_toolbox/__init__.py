"""My_Toolbox - Collection of utility tools and decorators.

Provides general-purpose utilities for string parsing, date manipulation, API resilience,
logging, data storage, validation, and error handling.
"""

# Decorators
from .my_decorators import (
    before_after, log_calls, requires, run_if,
    timing, memoize, throttle,
    validate_args, not_none, deprecated,
    singleton, timing_with_threshold, type_check,
    catch_exception
)

# String operations
from .string_ops import StringFunctions

# Date/Time operations
from .time_ops import DateFunctions

# API tools (rate limiting, retry, circuit breaker decorators)
from .api_tools import (
    RateLimiter, with_rate_limit,
    ExponentialBackoffPolicy, CircuitBreaker, retry_with_backoff
)

# Logging
from .log_tools import Logger, ContextLogger, StructuredLogger, MetricsLogger

# Directory/File operations
from .directory_tools import DataStorage

# Error handling (custom exception types)
from .error_handling import (
    ToolboxError,
    ConfigurationError,
    ValidationError,
    APIError,
    RateLimitError,
    AuthenticationError,
    ServerError,
    NotFoundError,
    TimeoutError,
    RetryExhaustedError,
    DataProcessingError,
    FileOperationError,
)

# Validation utilities
from .validation import (
    Validator,
    validate_email,
    validate_url,
    validate_phone,
    validate_json_schema,
    sanitize_input,
)

# Operator utilities (functional programming tools)
from .new_tools import OperatorTools

# Version
__version__ = "1.1.0"

__all__ = [
    # Decorators (core)
    "before_after",
    "log_calls",
    "requires",
    "run_if",
    # Decorators (performance & timing)
    "timing",
    "memoize",
    "throttle",
    "timing_with_threshold",
    # Decorators (validation & guards)
    "validate_args",
    "not_none",
    "type_check",
    # Decorators (patterns & maintenance)
    "deprecated",
    "singleton",
    "catch_exception",
    # String operations
    "StringFunctions",
    # Date/Time operations
    "DateFunctions",
    # API tools
    "RateLimiter",
    "with_rate_limit",
    "ExponentialBackoffPolicy",
    "CircuitBreaker",
    "retry_with_backoff",
    # Logging
    "Logger",
    "ContextLogger",
    "StructuredLogger",
    "MetricsLogger",
    # Directory/File operations
    "DataStorage",
    # Error handling
    "ToolboxError",
    "ConfigurationError",
    "ValidationError",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "ServerError",
    "NotFoundError",
    "TimeoutError",
    "RetryExhaustedError",
    "DataProcessingError",
    "FileOperationError",
    # Validation
    "Validator",
    "validate_email",
    "validate_url",
    "validate_phone",
    "validate_json_schema",
    "sanitize_input",
    # Operator utilities
    "OperatorTools",
    # Module references (for backward compatibility)
    "api_tools",
    "directory_tools",
    "gcp_tools",
    "git_tools",
    "kaggle_tools",
    "log_tools",
    "pdf_tools",
    "postgress_tools",
    "streamlit_tools",
    "string_ops",
    "time_ops",
    "my_decorators",
    "error_handling",
    "validation",
    "new_tools",
]

