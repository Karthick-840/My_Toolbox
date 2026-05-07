from datetime import datetime, timezone
from functools import wraps, lru_cache
from typing import Any, Callable, Optional, Dict
from time import perf_counter, time, sleep
import threading

Predicate = Callable[..., bool]


def before_after(
    before: Optional[Callable[..., Any]] = None,
    after: Optional[Callable[..., Any]] = None,
):
    """Create a decorator that runs callbacks before and after a function call."""

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if before:
                before(*args, **kwargs)
            result = func(*args, **kwargs)
            if after:
                after(result, *args, **kwargs)
            return result

        return wrapped

    return decorator


def run_if(predicate: Predicate, fallback: Any = "Function will not run"):
    """Run a function only when predicate(*args, **kwargs) is True."""

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not predicate(*args, **kwargs):
                return fallback
            return func(*args, **kwargs)

        return wrapped

    return decorator


def requires(predicate: Predicate, message: str = "Unauthorized"):
    """Authorization-style guard that raises PermissionError when check fails."""

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not predicate(*args, **kwargs):
                raise PermissionError(message)
            return func(*args, **kwargs)

        return wrapped

    return decorator


def log_calls(logfile: Optional[str] = "out.log", console: bool = True):
    """Return a decorator that logs function calls to console and optional file.

    Args:
        logfile: File path where call logs are appended. If None, file logging is disabled.
        console: Print logs to stdout when True.
    """

    def logging_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            log_string = f"[{timestamp} UTC] {func.__name__} was called"

            if console:
                print(log_string)

            if logfile:
                with open(logfile, "a", encoding="utf-8") as opened_file:
                    opened_file.write(log_string + "\n")

            return func(*args, **kwargs)

        return wrapped_function

    return logging_decorator


# ===== PERFORMANCE & TIMING =====

def timing(func: Callable) -> Callable:
    """Measure and print function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - start
        print(f"⏱️  {func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper


def memoize(func: Callable) -> Callable:
    """Cache function results (memoization). Works like functools.lru_cache."""
    cache: Dict[Any, Any] = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Create cache key from args and kwargs
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    wrapper.cache_clear = lambda: cache.clear()
    wrapper.cache_info = lambda: f"Cache size: {len(cache)}"
    return wrapper


def throttle(delay: float = 1.0):
    """Throttle function calls - allow only one call per `delay` seconds."""
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with lock:
                now = time()
                if now - last_called[0] < delay:
                    return None
                last_called[0] = now
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ===== VALIDATION & GUARDS =====

def validate_args(**validators: Callable[[Any], bool]):
    """Validate function arguments before execution.
    
    Example:
        @validate_args(x=lambda x: x > 0, name=lambda n: isinstance(n, str))
        def my_func(x, name):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function signature to match kwargs with param names
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            # Check kwargs validators
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    if not validator(kwargs[param_name]):
                        raise ValueError(f"Validation failed for parameter '{param_name}': {kwargs[param_name]}")
                elif param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        if not validator(args[idx]):
                            raise ValueError(f"Validation failed for parameter '{param_name}': {args[idx]}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def not_none(func: Callable) -> Callable:
    """Guard: Raise ValueError if any argument is None."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if None in args or None in kwargs.values():
            raise ValueError(f"{func.__name__}() received None argument(s)")
        return func(*args, **kwargs)
    return wrapper


# ===== DEPRECATION & MAINTENANCE =====

def deprecated(message: str = ""):
    """Mark function as deprecated. Prints warning on call."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            warning = f"⚠️  DEPRECATED: {func.__name__}() is deprecated"
            if message:
                warning += f" - {message}"
            print(warning)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===== SINGLETON PATTERN =====

def singleton(cls):
    """Make a class a singleton (only one instance allowed)."""
    instances = {}
    lock = threading.Lock()
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


# ===== TIMING WITH RESULT =====

def timing_with_threshold(threshold_ms: float = 1000.0):
    """Alert if function takes longer than threshold (in milliseconds)."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (perf_counter() - start) * 1000
            
            if elapsed_ms > threshold_ms:
                print(f"⚠️  {func.__name__} exceeded threshold: {elapsed_ms:.2f}ms > {threshold_ms}ms")
            else:
                print(f"✓ {func.__name__} completed: {elapsed_ms:.2f}ms")
            
            return result
        return wrapper
    return decorator


# ===== ARGUMENT TYPE CHECKING =====

def type_check(**expected_types):
    """Validate argument types at runtime.
    
    Example:
        @type_check(x=int, name=str, items=list)
        def my_func(x, name, items):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            for param_name, expected_type in expected_types.items():
                if param_name in kwargs:
                    actual = kwargs[param_name]
                    if not isinstance(actual, expected_type):
                        raise TypeError(f"Parameter '{param_name}' expected {expected_type.__name__}, got {type(actual).__name__}")
                elif param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        actual = args[idx]
                        if not isinstance(actual, expected_type):
                            raise TypeError(f"Parameter '{param_name}' expected {expected_type.__name__}, got {type(actual).__name__}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===== EXCEPTION HANDLING =====

def catch_exception(exception_type: type, fallback: Any = None):
    """Catch specific exception and return fallback value instead of raising."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                print(f"⚠️  Caught {exception_type.__name__}: {e}")
                return fallback
        return wrapper
    return decorator