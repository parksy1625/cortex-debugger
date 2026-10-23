"""M6 local model subprocess, bounded execution and restartable IPC.

One process caches the model across successful requests. Abort/timeout/resource
limit kills that process; a later job boots a new one. No shell, user-supplied
command, dynamic function imports or raw prompt logging is supported.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from typing import Any

import psutil


class WorkerCancelled(RuntimeError):
    pass


class WorkerTimeout(RuntimeError):
    pass


class WorkerMemoryExceeded(RuntimeError):
    pass


class WorkerExited(RuntimeError):
    pass


class ModelProcess:
    def __init__(
        self, timeout_seconds: float = 180.0, memory_limit_mb: int = 0,
        command: list[str] | None = None,
    ) -> None:
        if not 0.05 <= timeout_seconds <= 3600:
            raise ValueError("timeout_seconds must be between 0.05 and 3600")
        if not 0 <= memory_limit_mb <= 1048576:
            raise ValueError("memory_limit_mb must be in [0, 1048576]")
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.command = command or [sys.executable, "-u", "-m", "apps.api.model_worker"]
        self.process: subprocess.Popen | None = None
        self.messages: queue.Queue[str | None] = queue.Queue()
        self.lock = threading.RLock()
        self.model_loads = 0
        self.cache_hits = 0
        self.cached: dict[str, Any] | None = None

    def _launch(self) -> None:
        self.messages = queue.Queue()
        self.process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
            # Isolate descendants in their own Unix process group.
            start_new_session=(os.name == "posix"),
        )
        stdout = self.process.stdout
        assert stdout is not None
        mailbox = self.messages

        def reader() -> None:
            try:
                for line in stdout:
                    mailbox.put(line)
            finally:
                mailbox.put(None)

        threading.Thread(target=reader, daemon=True, name="cortex-ipc-reader").start()

    def stop(self) -> None:
        with self.lock:
            child = self.process
            self.process = None
            self.cached = None
        if child is None:
            return
        if child.poll() is None:
            try:
                parent = psutil.Process(child.pid)
                children = parent.children(recursive=True)
                for dependent in children:
                    dependent.kill()
            except (psutil.Error, ProcessLookupError):
                pass
            try:
                child.kill()
            except ProcessLookupError:
                pass
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                child.kill()
            except ProcessLookupError:
                pass
        for stream in (child.stdin, child.stdout):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass

    def _memory_bytes(self, child: subprocess.Popen) -> int:
        try:
            process = psutil.Process(child.pid)
            processes = [process, *process.children(recursive=True)]
            return sum(p.memory_info().rss for p in processes if p.is_running())
        except (psutil.Error, ProcessLookupError):
            return 0

    def execute(self, args: dict[str, Any], cancel: threading.Event) -> dict[str, Any]:
        if cancel.is_set():
            raise WorkerCancelled("Model operation was cancelled")
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self.stop()
                self._launch()
            child = self.process
            assert child is not None and child.stdin is not None
            try:
                child.stdin.write(json.dumps({"command": "pair", "args": args}) + "\n")
                child.stdin.flush()
            except (OSError, BrokenPipeError) as exc:
                self.stop()
                raise WorkerExited("Model process IPC write failed") from exc

        deadline = time.monotonic() + self.timeout_seconds
        while True:
            if cancel.is_set():
                self.stop()
                raise WorkerCancelled("Model operation was cancelled")
            if time.monotonic() >= deadline:
                self.stop()
                raise WorkerTimeout("Model execution exceeded configured deadline")
            if self.memory_limit_mb and self._memory_bytes(child) > self.memory_limit_mb * 1024 * 1024:
                self.stop()
                raise WorkerMemoryExceeded("Model process exceeded configured RSS budget")
            try:
                line = self.messages.get(timeout=0.05)
            except queue.Empty:
                if child.poll() is not None:
                    # The reader may still be delivering its final line.
                    continue
                continue
            if line is None:
                self.stop()
                if cancel.is_set():
                    raise WorkerCancelled("Model operation was cancelled")
                raise WorkerExited("Model process exited without a result")
            try:
                response = json.loads(line)
            except json.JSONDecodeError as exc:
                self.stop()
                raise WorkerExited("Model process returned invalid JSON") from exc
            if not isinstance(response, dict) or response.get("kind") not in ("result", "error"):
                self.stop()
                raise WorkerExited("Model process returned an invalid message")
            if cancel.is_set():
                self.stop()
                raise WorkerCancelled("Model operation was cancelled")
            if response["kind"] == "error":
                # Worker error messages contain *only* exception class names.
                raise WorkerExited(
                    "Model execution failed in isolated worker ("
                    + str(response.get("error_type", "UnknownError"))[:60] + ")"
                )
            result = response.get("data")
            if not isinstance(result, dict):
                self.stop()
                raise WorkerExited("Model process returned invalid experiment data")
            execution = result.get("execution") or {}
            if execution.get("model_cache_hit"):
                self.cache_hits += 1
            else:
                self.model_loads += 1
            model = result.get("model") or {}
            self.cached = {
                "model_id": model.get("id"),
                "revision": model.get("revision"),
                "device": model.get("device"),
            }
            return result

    def status(self) -> dict[str, Any]:
        child = self.process
        loaded = child is not None and child.poll() is None and self.cached is not None
        return {
            "loaded": loaded,
            "model_id": self.cached["model_id"] if loaded else None,
            "revision": self.cached["revision"] if loaded else None,
            "device": self.cached["device"] if loaded else None,
            "model_loads": self.model_loads,
            "cache_hits": self.cache_hits,
            "isolated": True,
            "worker_pid": child.pid if child and child.poll() is None else None,
            "memory_budget_mb": self.memory_limit_mb,
            "timeout_seconds": self.timeout_seconds,
        }
