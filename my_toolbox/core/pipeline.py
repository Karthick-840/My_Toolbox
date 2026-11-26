"""Pipeline utilities: retry with backoff, step run logging, checkpoints. Stdlib only."""

import functools
import json
import logging
import random
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Type

log = logging.getLogger("my_toolbox.pipeline")


def retry(attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, jitter: float = 0.1,
          exceptions: Tuple[Type[BaseException], ...] = (Exception,),
          sleep: Callable[[float], None] = time.sleep):
    """Retry a function with exponential backoff; re-raises the last error."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == attempts:
                        raise
                    log.warning("%s failed (%s/%s): %s; retrying in %.2fs",
                                func.__name__, attempt, attempts, exc, wait)
                    sleep(wait + random.uniform(0, jitter * wait))
                    wait *= backoff
        return wrapper
    return decorator


class PipelineRun:
    """Records each step's status, duration and row count; usable as a context per step."""

    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.steps: List[Dict] = []

    @contextmanager
    def step(self, step_name: str):
        record: Dict = {"step": step_name, "status": "running", "rows": None}
        self.steps.append(record)
        start = time.perf_counter()
        try:
            yield record
            record["status"] = "ok"
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            record["seconds"] = round(time.perf_counter() - start, 4)
            log.info("%s/%s %s rows=%s %.2fs", self.name, step_name, record["status"],
                     record["rows"], record["seconds"])

    def summary(self) -> Dict:
        return {
            "pipeline": self.name,
            "ok": all(s["status"] == "ok" for s in self.steps),
            "total_seconds": round(sum(s.get("seconds", 0) for s in self.steps), 4),
            "steps": self.steps,
        }


class Checkpoint:
    """JSON-file store of completed steps so a rerun can skip them."""

    def __init__(self, path):
        self.path = Path(path)
        self._data: Dict[str, Dict] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def done(self, key: str) -> bool:
        return key in self._data

    def mark(self, key: str, info: Optional[Dict] = None) -> None:
        self._data[key] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **(info or {})}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def clear(self, key: Optional[str] = None) -> None:
        self._data.pop(key, None) if key else self._data.clear()
        self.path.write_text(json.dumps(self._data), encoding="utf-8") if self.path.exists() else None

    def run_once(self, key: str, func: Callable, *args, **kwargs):
        """Run func unless key is already marked done; returns None when skipped."""
        if self.done(key):
            return None
        result = func(*args, **kwargs)
        self.mark(key)
        return result
