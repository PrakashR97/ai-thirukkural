"""In-memory sliding-window limiter for *paid* generations (cache hits are never limited).

Single-process only (one uvicorn worker), which is how the Docker image runs.
"""
import math
import threading
import time
from collections import defaultdict, deque
from typing import Callable

HOUR = 3600.0
DAY = 86400.0


class RateLimiter:
    def __init__(self, per_visitor_per_hour: int, global_per_day: int,
                 clock: Callable[[], float] = time.monotonic):
        self.per_visitor = per_visitor_per_hour
        self.per_day = global_per_day
        self._clock = clock
        self._lock = threading.Lock()
        self._visitors: dict[str, deque[float]] = defaultdict(deque)
        self._global: deque[float] = deque()

    @staticmethod
    def _trim(q: deque, window: float, now: float) -> None:
        while q and now - q[0] >= window:
            q.popleft()

    def acquire(self, visitor: str) -> tuple[bool, int, str]:
        """Try to spend one generation. Returns (allowed, retry_after_seconds, reason)."""
        with self._lock:
            now = self._clock()
            if self.per_day > 0:
                self._trim(self._global, DAY, now)
                if len(self._global) >= self.per_day:
                    return False, math.ceil(DAY - (now - self._global[0])), "daily"
            if self.per_visitor > 0:
                q = self._visitors[visitor]
                self._trim(q, HOUR, now)
                if len(q) >= self.per_visitor:
                    return False, math.ceil(HOUR - (now - q[0])), "visitor"
                q.append(now)
            self._global.append(now)
            return True, 0, ""
