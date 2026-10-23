"""Process-local, single-instance model cache for Cortex's serialized worker.

One bridge is retained in memory at a time. It is keyed by (model, revision,
device), never by user prompt. Cache access is guarded by an RLock; the caller
holds the same lock through inference to avoid concurrent hook mutations.
Do not run more than one Uvicorn worker when using process-local job queues.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

Key = tuple[str, str, str]


class SingleModelCache:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self._key: Key | None = None
        self._model: Any = None
        self._loads = 0
        self._hits = 0

    def load(self, key: Key, factory: Callable[[], Any]) -> tuple[Any, bool, float]:
        with self.lock:
            if self._key == key and self._model is not None:
                self._hits += 1
                return self._model, True, 0.0
            started = time.monotonic()
            # Failure doesn't retain partially constructed model or stale key.
            self._model = None
            self._key = None
            model = factory()
            model.eval()
            duration = time.monotonic() - started
            self._key = key
            self._model = model
            self._loads += 1
            return model, False, round(duration, 6)

    def status(self) -> dict[str, Any]:
        with self.lock:
            return {
                "loaded": self._model is not None,
                "model_id": self._key[0] if self._key else None,
                "revision": self._key[1] if self._key else None,
                "device": self._key[2] if self._key else None,
                "model_loads": self._loads,
                "cache_hits": self._hits,
            }

    def clear(self) -> None:
        with self.lock:
            self._model = None
            self._key = None


MODEL_CACHE = SingleModelCache()
