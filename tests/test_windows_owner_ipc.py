"""Real Windows named-pipe IPC tests: ACL, client SID, framing, lifecycle.

Windows GitHub-hosted runner exercises OS named pipes; no model needed.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows SID tests only")


@pytest.fixture
def pipe(tmp_path):
    from apps.api.owner_pipe_windows import WindowsOwnerControl

    seen = []
    server = WindowsOwnerControl(
        tmp_path / "data", lambda: {"loaded": False},
        lambda job_id: seen.append(job_id) is None,
    )
    server.start()
    try:
        yield server, seen
    finally:
        server.close()


def test_actual_windows_token_and_named_pipe_round_trip(pipe, tmp_path):
    from apps.api.owner_pipe_windows import request_control_name

    server, seen = pipe
    assert request_control_name(server.name, {"command": "status"}) == {
        "ok": True, "data": {"loaded": False}
    }
    jid = "ab" * 16
    assert request_control_name(server.name, {"command": "cancel", "id": jid}) == {
        "ok": True, "cancelled": True
    }
    assert seen == [jid]
    assert request_control_name(server.name, {"command": "delete"})["error"] == "unknown_command"
    assert seen == [jid]


def test_windows_pipe_dacl_contains_only_owner_sid(pipe):
    import win32security

    from apps.api.owner_pipe_windows import _security_attributes

    server, _ = pipe
    assert server.owner_sid
    descriptor = _security_attributes().SECURITY_DESCRIPTOR
    acl = descriptor.GetSecurityDescriptorDacl()
    assert acl is not None and acl.GetAceCount() == 1
    ace = acl.GetAce(0)
    assert win32security.ConvertSidToStringSid(ace[2]) == server.owner_sid


def test_client_impersonation_sid_mismatch_fails_closed(pipe, monkeypatch):
    from apps.api import owner_pipe_windows

    server, seen = pipe
    monkeypatch.setattr(owner_pipe_windows, "_client_sid", lambda _handle: "S-1-5-7")
    result = owner_pipe_windows.request_control_name(
        server.name, {"command": "cancel", "id": "12" * 16}
    )
    assert result["error"] == "peer_denied"
    assert seen == []


def test_excessive_message_and_invalid_command_are_rejected(pipe):
    from apps.api.owner_pipe_windows import request_control_name

    server, seen = pipe
    assert request_control_name(server.name, {
        "command": "cancel", "id": "x" * 8200
    })["error"] == "bad_or_oversized_request"
    assert request_control_name(server.name, {
        "command": "cancel", "id": "not-hex"
    })["error"] == "unknown_command"
    assert seen == []


def test_second_service_cannot_steal_running_named_pipe(pipe):
    import pywintypes

    from apps.api.owner_pipe_windows import WindowsOwnerControl

    current, _ = pipe
    contender = WindowsOwnerControl(
        current.name, lambda: {}, lambda _id: False
    )
    # Use same configured name regardless of separate tmpdir suffix.
    contender.name = current.name
    with pytest.raises(pywintypes.error):
        contender.start()


def test_separate_windows_client_process(pipe, tmp_path):
    server, _ = pipe
    subprocess_client = (
        "import json,sys;"
        "from apps.api.owner_pipe_windows import request_control_name;"
        "print(json.dumps(request_control_name(sys.argv[1], {'command':'status'})))"
    )
    r = subprocess.run(
        [sys.executable, "-c", subprocess_client, server.name],
        capture_output=True, text=True, timeout=12, check=False,
    )
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["data"]["loaded"] is False


def test_fastapi_lifespan_starts_and_stops_owner_pipe(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from apps.api.main import app
    from apps.api.owner_pipe_windows import pipe_name, request_control_name

    directory = tmp_path / "data"
    monkeypatch.setenv("CORTEX_DATA_DIR", str(directory))
    monkeypatch.setenv("CORTEX_OWNER_IPC", "1")
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert request_control_name(pipe_name(directory), {"command": "status"})["ok"]
    # Pipe instance handle must have been closed on shutdown.
