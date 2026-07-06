import time
from collections import defaultdict
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = self._clock()
        hits = self._hits[key]
        cutoff = now - self._window_seconds
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= self._max_requests:
            return False
        hits.append(now)
        return True
