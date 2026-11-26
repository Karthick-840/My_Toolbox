"""
API tools for making resilient API calls with rate limiting, retry logic, and circuit breaking.

Classes:
    RateLimiter: Token bucket rate limiting.
    ExponentialBackoffPolicy: Exponential backoff with jitter for retry strategies.
    CircuitBreaker: Circuit breaker pattern for fault tolerance.
    ApiTools: Legacy high-level API call handler (Rapid API).

Functions:
    with_rate_limit: Decorator to apply rate limiting to a function.
    retry_with_backoff: Decorator to apply exponential backoff + circuit breaker.
"""

import time
import random
from typing import Optional, Callable, Any, TypeVar
from threading import Lock
from enum import Enum
from functools import wraps

from .error_handling import (
    APIError, RateLimitError, AuthenticationError, ServerError, 
    TimeoutError as ToolboxTimeoutError, RetryExhaustedError
)

T = TypeVar('T')


class RateLimiter:
    """Token bucket rate limiter. Thread-safe."""
    
    def __init__(self, requests_per_minute: int):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute allowed
        """
        self.min_interval = 60.0 / requests_per_minute
        self.lock = Lock()
        self.last_ts = 0.0

    def wait(self):
        """Wait until next request is allowed."""
        with self.lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self.last_ts)
            if wait > 0:
                time.sleep(wait)
            self.last_ts = time.monotonic()


def with_rate_limit(limiter: RateLimiter):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        limiter: RateLimiter instance
        
    Returns:
        Decorated function
        
    Example:
        >>> limiter = RateLimiter(requests_per_minute=60)
        >>> @with_rate_limit(limiter)
        ... def fetch_api(url): ...
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return fn(*args, **kwargs)
        return wrapper
    return deco


class ExponentialBackoffPolicy:
    """Exponential backoff with jitter for retry strategies."""
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 32.0,
        multiplier: float = 2.0,
        max_retries: int = 3,
        jitter: bool = True,
    ):
        """
        Initialize exponential backoff policy.
        
        Args:
            initial_delay: Starting delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Multiplier for each retry
            max_retries: Maximum number of retries
            jitter: Add randomization (0-25%) to prevent thundering herd
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.max_retries = max_retries
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add 0-25% jitter
            jitter_amount = delay * random.uniform(0, 0.25)
            delay += jitter_amount
        
        return delay
    
    def should_retry(self, attempt: int) -> bool:
        """Check if should retry based on attempt count."""
        return attempt < self.max_retries


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    
    Prevents cascading failures by failing fast after threshold is reached.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "CircuitBreaker",
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Consecutive failures before opening circuit
            recovery_timeout: Seconds before attempting recovery (HALF_OPEN)
            name: Descriptive name for this breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = Lock()
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            APIError: If circuit is open or function fails
        """
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise APIError(f"Circuit breaker '{self.name}' is OPEN (failing fast)")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout elapsed."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            self.failure_count = 0
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 2:  # 2 successes to close circuit
                    self.state = CircuitBreakerState.CLOSED
                    self.success_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
    
    def get_state(self) -> str:
        """Get current circuit breaker state."""
        with self.lock:
            return self.state.value


def retry_with_backoff(
    backoff_policy: Optional[ExponentialBackoffPolicy] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
):
    """
    Decorator to apply exponential backoff + circuit breaker to a function.
    
    Args:
        backoff_policy: ExponentialBackoffPolicy instance (defaults to sensible values)
        circuit_breaker: CircuitBreaker instance (optional)
        
    Returns:
        Decorated function
        
    Example:
        >>> @retry_with_backoff()
        ... def fetch_api(url):
        ...     return requests.get(url)
    """
    if backoff_policy is None:
        backoff_policy = ExponentialBackoffPolicy()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(backoff_policy.max_retries + 1):
                try:
                    if circuit_breaker:
                        return circuit_breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                
                except (RateLimitError, ServerError, ToolboxTimeoutError) as e:
                    # Retryable errors
                    last_exception = e
                    
                    if not backoff_policy.should_retry(attempt):
                        break
                    
                    delay = backoff_policy.get_delay(attempt)
                    time.sleep(delay)
                
                except (AuthenticationError, APIError) as e:
                    # Non-retryable errors
                    raise
            
            # All retries exhausted
            if last_exception:
                raise RetryExhaustedError(
                    str(last_exception),
                    attempts=backoff_policy.max_retries + 1
                )
            raise APIError("Retry logic failed with no exception captured")
        
        return wrapper
    return decorator




class ApiTools:
    """
    High-level API call handler with response parsing.
    Specifically designed to work with Rapid API endpoints.
    
    Methods:
        rapid_api_calls: Make API call with URL, headers, and optional parameters.
        handle_status_code: Log and interpret HTTP status codes.
    """
    
    def __init__(self, logger):
        """Initialize with logger instance."""
        self.logger = logger.info('API Tools Initiated.')
        self.logger = logger.getChild(__name__)

    def rapid_api_calls(self, rapid_api_dict, logger, params=None):
        """
        Make a call to a Rapid API endpoint with given parameters and headers.
        
        Args:
            rapid_api_dict: Dict with 'url' and 'headers' keys for the API call
            logger: Logger instance to log information and errors
            params: Optional dict of query parameters
            
        Returns:
            JSON response dict. If response contains 'data' field, returns that content.
            
        Raises:
            Exception: If an error occurs during the API call
        """
        import requests
        
        time.sleep(1)
        response_json = ""
        url = rapid_api_dict.get("url")
        headers = rapid_api_dict.get("headers")
        self.logger.info(f"Initiating Call for {url}")
        try:
            if not headers:
                response = requests.get(url, verify=False, timeout=10)
            elif params:
                response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
            else:
                response = requests.get(url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Status code: {response.status_code}: Rapid API call Successful")
                response_json = response.json()
                if 'data' in response_json:
                    response_json = response_json['data']
            else:
                self.handle_status_code(response.status_code)
        except Exception as e:
            logger.info(f"An error occurred: {e}")

        return response_json

    def handle_status_code(self, response_status_code):
        """Log and handle different HTTP status codes."""
        status_code_messages = {
            400: "Bad Request: The server could not understand the request.",
            401: "Unauthorized: Access is denied due to invalid credentials.",
            403: "Forbidden: You do not have permission to access this resource.",
            404: "Not Found: The requested resource could not be found.",
            429: "Too Many Requests: You have exceeded the rate limit.",
            500: "Internal Server Error: The server encountered an error."
        }

        if response_status_code in status_code_messages:
            self.logger.info(f"Status code: {response_status_code}: {status_code_messages[response_status_code]}")
        else:
            self.logger.info(f"Status code: {response_status_code}: Unexpected status code")

