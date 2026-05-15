import threading
import time


class RateLimiter:
    def __init__(self, requests_per_second: float = 5.0):
        self._rps = requests_per_second
        self._interval = 1.0 / requests_per_second
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()

    def acquire(self) -> None:
        self._pause_event.wait()
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._interval:
                time.sleep(self._interval - elapsed)
            self._last_call = time.monotonic()

    def set_rps(self, rps: float) -> None:
        with self._lock:
            self._rps = max(0.1, rps)
            self._interval = 1.0 / self._rps

    def pause(self) -> None:
        self._paused = True
        self._pause_event.clear()

    def resume(self) -> None:
        self._paused = False
        self._pause_event.set()

    def is_paused(self) -> bool:
        return self._paused
