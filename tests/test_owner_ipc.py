"""M12 POSIX peer-verified local control channel behavior."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import stat

import pytest
from fastapi.testclient import TestClient

from apps.api.owner_ipc import (
    MAX_CONTROL_BYTES,
    OwnerControl,
    control_path,
    request_control,
)

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX Unix socket only")


@pytest.fixture
def control(tmp_path):
    directory = tmp_path / "experiments"
    command_ids = []

    server = OwnerControl(
        directory,
        get_status=lambda: {"model": {"loaded": False, "device": None}},
        cancel_job=lambda job_id: command_ids.append(job_id) is None,
    )
    server.start()
    try:
        yield server, directory, command_ids
    finally:
        server.close()


def test_owner_uid_and_strict_directory_socket_permissions(control):
    server, directory, _ = control
    assert stat.S_IMODE(server.path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(server.path.stat().st_mode) == 0o600
    assert server.path.stat().st_uid == os.geteuid()
    assert request_control(directory, "status") == {
        "ok": True, "data": {"model": {"loaded": False, "device": None}}
    }
    assert control_path(directory) == server.path


def test_cancel_validates_format_and_no_arbitrary_dispatch(control):
    _, directory, invoked = control
    job_id = "ab" * 16
    assert request_control(directory, "cancel", job_id) == {
        "ok": True, "cancelled": True
    }
    assert invoked == [job_id]
    assert request_control(directory, "cancel", "bad!")["error"] == "unknown_command"
    assert request_control(directory, "delete")["error"] == "unknown_command"
    assert invoked == [job_id]


def test_os_reported_uid_is_enforced(control, monkeypatch):
    from apps.api import owner_ipc

    _, directory, _ = control
    # The kernel UID is normally read from SO_PEERCRED/getpeereid; pretend it
    # reports another user to exercise the rejection path.
    monkeypatch.setattr(owner_ipc, "_peer_uid", lambda _conn: os.geteuid() + 1)
    assert request_control(directory, "status")["error"] == "peer_denied"


def test_oversize_request_is_rejected_without_dispatch(control):
    server, directory, invoked = control
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(server.path))
        client.sendall(b"x" * (MAX_CONTROL_BYTES + 5) + b"\n")
        with client.makefile("rb") as stream:
            message = json.loads(stream.readline(MAX_CONTROL_BYTES + 1))
    assert message["error"] == "request_too_large"
    assert invoked == []


def test_refuses_symlink_and_open_permission_socket_directory(tmp_path):
    from apps.api.owner_ipc import _secure_directory

    world_readable = tmp_path / "permissive"
    world_readable.mkdir(mode=0o755)
    world_readable.chmod(0o755)
    with pytest.raises(PermissionError, match="mode 0700"):
        _secure_directory(world_readable)
    symlink = tmp_path / "link"
    symlink.symlink_to(world_readable, target_is_directory=True)
    with pytest.raises(PermissionError, match="symlink"):
        _secure_directory(symlink)


def test_does_not_replace_running_socket_or_untrusted_file(tmp_path):
    directory = tmp_path / "data"
    server1 = OwnerControl(directory, lambda: {}, lambda _id: False)
    server1.start()
    try:
        server2 = OwnerControl(directory, lambda: {}, lambda _id: False)
        with pytest.raises(RuntimeError, match="already running"):
            server2.start()
    finally:
        server1.close()
    file_path = control_path(directory)
    file_path.write_text("not a socket", encoding="utf-8")
    with pytest.raises(PermissionError, match="untrusted IPC path"):
        OwnerControl(directory, lambda: {}, lambda _id: False).start()


def test_socket_lifecycle_app_integration(tmp_path, monkeypatch):
    from apps.api.main import app

    data_dir = tmp_path / "cortex"
    monkeypatch.setenv("CORTEX_OWNER_IPC", "1")
    monkeypatch.setenv("CORTEX_DATA_DIR", str(data_dir))
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        response = request_control(data_dir, "status")
        assert response["ok"] is True
        assert "loaded" in response["data"]
    assert not control_path(data_dir).exists()


def test_separate_process_peer_uid_is_validated(control):
    """The client is a second OS process, not a direct in-memory call."""
    _, directory, _ = control
    result = subprocess.run(
        [
            sys.executable, "-m", "apps.api.owner_ipc", "status",
            "--data-dir", str(directory),
        ],
        capture_output=True, text=True, timeout=8, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["model"]["loaded"] is False
