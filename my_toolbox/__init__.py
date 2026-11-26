"""My_Toolbox - Collection of utility tools and decorators.

Provides general-purpose utilities for string parsing, date manipulation, API resilience,
logging, data storage, validation, and error handling.
"""

# Decorators
# API tools (rate limiting, retry, circuit breaker decorators)
from .api_tools import (
    CircuitBreaker,
    ExponentialBackoffPolicy,
    RateLimiter,
    retry_with_backoff,
    with_rate_limit,
)

# Directory/File operations
from .directory_tools import DataStorage

# Error handling (custom exception types)
from .error_handling import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataProcessingError,
    FileOperationError,
    NotFoundError,
    RateLimitError,
    RetryExhaustedError,
    ServerError,
    TimeoutError,
    ToolboxError,
    ValidationError,
)

# Logging
from .log_tools import ContextLogger, Logger, MetricsLogger, StructuredLogger
from .my_decorators import (
    before_after,
    catch_exception,
    deprecated,
    log_calls,
    memoize,
    not_none,
    requires,
    run_if,
    singleton,
    throttle,
    timing,
    timing_with_threshold,
    type_check,
    validate_args,
)

# Operator utilities (functional programming tools)
from .new_tools import OperatorTools

# String operations
from .string_ops import StringFunctions

# Date/Time operations
from .time_ops import DateFunctions

# Validation utilities
from .validation import (
    Validator,
    sanitize_input,
    validate_email,
    validate_json_schema,
    validate_phone,
    validate_url,
)

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

