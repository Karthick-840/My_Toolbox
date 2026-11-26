"""
Centralized exception hierarchy for my_toolbox and dependent projects.

Provides typed, domain-specific exceptions for cleaner error handling.
"""


class ToolboxError(Exception):
    """Base exception for all my_toolbox errors."""
    pass


class ConfigurationError(ToolboxError):
    """Raised when configuration is missing or invalid."""
    pass


class ValidationError(ToolboxError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.field:
            return f"Validation error in '{self.field}': {self.message}"
        return self.message


class APIError(ToolboxError):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = None, response: str = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class RateLimitError(APIError):
    """Raised when API rate limit (429) is hit."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class AuthenticationError(APIError):
    """Raised for authentication failures (401, 403)."""
    pass


class ServerError(APIError):
    """Raised for server errors (500, 503, 504)."""
    pass


class NotFoundError(APIError):
    """Raised for not found errors (404)."""
    pass


class TimeoutError(APIError):
    """Raised when API call times out."""
    pass


class RetryExhaustedError(APIError):
    """Raised when retries are exhausted."""
    
    def __init__(self, message: str, attempts: int = None):
        self.attempts = attempts
        full_msg = f"{message} (after {attempts} attempts)" if attempts else message
        super().__init__(full_msg)


class DataProcessingError(ToolboxError):
    """Raised when data processing fails."""
    pass


class FileOperationError(ToolboxError):
    """Raised when file operations fail."""
    pass
