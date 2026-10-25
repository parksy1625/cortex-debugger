"""M6 real subprocess lifecycle: timeout, cancellation, reuse and memory guard.

All experiments use a minimal deterministic stdin/stdout subprocess; no model
download required. Live GPT-2 is tested separately in CI.
"""

from __future__ import annotations

import json
import sys
import threading
import time

import pytest

from apps.api.experiments import ExperimentManager
from apps.api.model_process import (
    ModelProcess,
    WorkerCancelled,
    WorkerMemoryExceeded,
    WorkerTimeout,
)

STUB = """
import json, sys, time
n = 0
for line in sys.stdin:
    req = json.loads(line)
    args = req["args"]
    time.sleep(args.get("delay", 0.0))
    result = {
      "status": "pass",
      "model": {"id": "openai-community/gpt2", "revision": "abc", "device": "cpu"},
      "scores": {"recovery": 0.5},
      "execution": {"model_cache_hit": n > 0}
    }
    n += 1
    print(json.dumps({"kind": "result", "data": result}), flush=True)
"""


def process(timeout: float = 3, memory_mb: int = 0) -> ModelProcess:
    return ModelProcess(
        timeout_seconds=timeout,
        memory_limit_mb=memory_mb,
        command=[sys.executable, "-u", "-c", STUB],
    )


def test_process_reuses_child_then_restart():
    client = process()
    try:
        a = client.execute({}, threading.Event())
        pid = client.status()["worker_pid"]
        b = client.execute({}, threading.Event())
        assert a["execution"]["model_cache_hit"] is False
        assert b["execution"]["model_cache_hit"] is True
        assert client.status()["model_loads"] == 1
        assert client.status()["cache_hits"] == 1
        assert client.status()["worker_pid"] == pid
        client.stop()
        assert client.status()["loaded"] is False
        client.execute({}, threading.Event())
        assert client.status()["worker_pid"] != pid
    finally:
        client.stop()


def test_subprocess_timeout_kills_worker_and_allows_recovery():
    client = process(timeout=0.15)
    try:
        with pytest.raises(WorkerTimeout):
            client.execute({"delay": 2}, threading.Event())
        assert client.status()["worker_pid"] is None
        assert client.execute({}, threading.Event())["status"] == "pass"
    finally:
        client.stop()


def test_running_cancel_kills_worker_and_next_job_recovers():
    client = process(timeout=3)
    event = threading.Event()
    errors = []

    def run():
        try:
            client.execute({"delay": 2}, event)
        except Exception as exc:
            errors.append(exc)

    t = threading.Thread(target=run)
    t.start()
    deadline = time.monotonic() + 2
    while client.status()["worker_pid"] is None and time.monotonic() < deadline:
        time.sleep(.01)
    event.set()
    client.stop()
    t.join(timeout=3)
    assert not t.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], WorkerCancelled)
    try:
        assert client.execute({}, threading.Event())["status"] == "pass"
    finally:
        client.stop()


def test_memory_budget_is_enforced_by_parent_monitor():
    client = process(timeout=3, memory_mb=1)
    try:
        with pytest.raises(WorkerMemoryExceeded):
            client.execute({"delay": 2}, threading.Event())
        assert client.status()["worker_pid"] is None
    finally:
        client.stop()


def test_manager_running_job_is_cancellable_and_restartable(tmp_path):
    from apps.api.experiments import default_runner

    manager = ExperimentManager(tmp_path / "job.sqlite3", runner=default_runner)
    manager.worker = process(timeout=5)
    params = {
        "clean": "secret", "corrupted": "notsecret", "device": "cpu",
        "layer": 0, "token_index": 0, "delay": 2,
    }
    try:
        first = manager.submit(params)["id"]
        deadline = time.monotonic() + 3
        while manager.get(first)["status"] != "running" and time.monotonic() < deadline:
            time.sleep(.01)
        assert manager.get(first)["status"] == "running"
        assert manager.cancel(first) is True
        assert manager.get(first)["status"] == "cancelled"
        params["delay"] = 0
        second = manager.submit(params)["id"]
        deadline = time.monotonic() + 3
        while manager.get(second)["status"] not in ("completed", "failed") and time.monotonic() < deadline:
            time.sleep(.01)
        assert manager.get(second)["status"] == "completed"
        assert "secret" not in json.dumps(manager.get(second))
    finally:
        manager.shutdown()


def test_untrusted_worker_cannot_emit_unbounded_ipc():
    """A malicious or corrupted child may never allocate an unlimited line."""
    from apps.api.model_process import MAX_IPC_MESSAGE_CHARS, WorkerExited

    script = (
        "import sys; sys.stdin.readline();"
        "sys.stdout.write('x' * ("
        + str(MAX_IPC_MESSAGE_CHARS + 100)
        + ") + '\\n');sys.stdout.flush()"
    )
    child = ModelProcess(
        timeout_seconds=5,
        command=[sys.executable, "-u", "-c", script],
    )
    try:
        with pytest.raises(WorkerExited, match="exceeded safe IPC size"):
            child.execute({}, threading.Event())
        assert child.status()["worker_pid"] is None
    finally:
        child.stop()
