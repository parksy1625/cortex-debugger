"""Serialized local experiment execution; SQLite stores no raw prompts."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def default_runner(args: dict[str, Any]) -> dict[str, Any]:
    from cortex_engine.pairing import run_gpt2_pair
    return run_gpt2_pair(**args)

class QueueFull(Exception):
    pass

class NotCancellable(Exception):
    pass

class ExperimentManager:
    def __init__(self, path: Path, runner: Callable[[dict[str, Any]], dict[str, Any]] = default_runner, max_outstanding: int = 3) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self.max_outstanding = max_outstanding
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cortex-model")
        self.futures: dict[str, Future] = {}
        with self._db() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS experiments ("
                "id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, configuration TEXT NOT NULL, "
                "result TEXT, error TEXT)"
            )

    def _db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _update(self, experiment_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
        with self._db() as conn:
            conn.execute(
                "UPDATE experiments SET status=?, updated_at=?, result=?, error=? WHERE id=?",
                (status, utcnow(), json.dumps(result, allow_nan=False) if result is not None else None, error, experiment_id),
            )

    def submit(self, request_data: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            self.futures = {key: future for key, future in self.futures.items() if not future.done()}
            if len(self.futures) >= self.max_outstanding:
                raise QueueFull("Model experiment queue is full (1 running, 2 waiting).")
            experiment_id = uuid.uuid4().hex
            safe = {"model_id": "openai-community/gpt2", "device": request_data["device"],
                    "layer": request_data["layer"], "token_index": request_data["token_index"],
                    "revision": request_data.get("revision")}
            now = utcnow()
            with self._db() as conn:
                conn.execute(
                    "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, NULL, NULL)",
                    (experiment_id, "queued", now, now, json.dumps(safe)),
                )
            try:
                self.futures[experiment_id] = self.executor.submit(self._execute, experiment_id, request_data)
            except RuntimeError:
                self._update(experiment_id, "failed", error="Model worker is unavailable")
                raise
            return {"id": experiment_id, "status": "queued", "created_at": now}

    def _execute(self, experiment_id: str, request_data: dict[str, Any]) -> None:
        self._update(experiment_id, "running")
        try:
            result = self.runner(request_data)
            status = "completed" if result.get("status") == "pass" else "failed"
            self._update(experiment_id, status, result=result,
                         error="Identity control failed" if status == "failed" else None)
        except Exception as exc:
            # Model libraries may echo private prompts in exception messages.
            self._update(experiment_id, "failed",
                         error=f"Model execution failed ({type(exc).__name__}); inspect server logs locally")

    def get(self, experiment_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "status": row["status"], "created_at": row["created_at"],
                "updated_at": row["updated_at"], "configuration": json.loads(row["configuration"]),
                "result": json.loads(row["result"]) if row["result"] else None, "error": row["error"]}

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT id, status, created_at, updated_at, configuration "
                "FROM experiments ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"id": row["id"], "status": row["status"],
                 "created_at": row["created_at"], "updated_at": row["updated_at"],
                 "configuration": json.loads(row["configuration"])} for row in rows]

    def cancel(self, experiment_id: str) -> bool:
        with self.lock:
            record = self.get(experiment_id)
            if record is None:
                raise KeyError(experiment_id)
            future = self.futures.get(experiment_id)
            if future is None or record["status"] != "queued" or not future.cancel():
                raise NotCancellable("Only queued jobs can be cancelled; running model computation cannot be interrupted safely")
            self._update(experiment_id, "cancelled")
            return True

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True, cancel_futures=True)
