"""Platform-independent protocol checks for the Windows owner-control pipe.

The real ACL, kernel SID and named-pipe lifecycle remain Windows-only tests.
These tests exercise parsing and dispatch on Linux/macOS CI as well.
"""

from __future__ import annotations

import json

import pytest

from apps.api import owner_pipe_windows as pipe


def test_windows_dispatch_strict_commands_without_native_pipe():
    cancelled = []
    service = object.__new__(pipe.WindowsOwnerControl)
    service.get_status = lambda: {"model": "unloaded"}
    service.cancel_job = lambda job_id: cancelled.append(job_id) is None

    assert service._dispatch({"command": "status"}) == {
        "ok": True, "data": {"model": "unloaded"}
    }
    assert service._dispatch({"command": "status", "extra": True})["ok"] is False
    assert service._dispatch({"command": "cancel", "id": "ab" * 16}) == {
        "ok": True, "cancelled": True
    }
    assert cancelled == ["ab" * 16]
    for invalid in (None, {}, {"command": "delete"},
                    {"command": "cancel", "id": "AB" * 16},
                    {"command": "cancel", "id": 12},
                    {"command": "cancel", "id": "ab" * 16, "extra": 1}):
        assert service._dispatch(invalid)["ok"] is False
    assert cancelled == ["ab" * 16]


@pytest.mark.parametrize("payload", [
    b"not-json\n",
    b'[]\n',
    b'{"command":"status"}',
    b'{"command":"status"}\n' + b"x" * pipe.MAX_CONTROL_BYTES,
    b"\xff\n",
])
def test_windows_read_rejects_invalid_framing_on_any_platform(monkeypatch, payload):
    class FakeWin32File:
        @staticmethod
        def ReadFile(_handle, _size):
            return 0, payload

    class FakeError(Exception):
        winerror = 0

    monkeypatch.setattr(pipe, "_win32", lambda: (type("Errors", (), {"error": FakeError}),
                                                None, None, FakeWin32File, None, None))
    assert pipe._read_request(None) is None


def test_windows_read_accepts_valid_json_object_on_any_platform(monkeypatch):
    class FakeWin32File:
        @staticmethod
        def ReadFile(_handle, _size):
            return 0, (json.dumps({"command": "status"}) + "\n").encode()

    monkeypatch.setattr(pipe, "_win32", lambda: (object(), None, None,
                                                FakeWin32File, None, None))
    assert pipe._read_request(None) == {"command": "status"}


def test_windows_request_size_checked_before_client_connect(monkeypatch):
    class NoClientOpen:
        @staticmethod
        def CreateFile(*_args, **_kwargs):
            pytest.fail("oversized request opened a named pipe")

    monkeypatch.setattr(pipe, "_win32", lambda: (None, None, object(),
                                                NoClientOpen, None, None))
    with pytest.raises(ValueError, match="Oversize named-pipe request"):
        pipe.request_control_name("unused", {"command": "cancel", "id": "a" * 8200})
