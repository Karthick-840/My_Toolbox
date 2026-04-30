from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

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
