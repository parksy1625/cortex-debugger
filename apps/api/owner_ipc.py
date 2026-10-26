"""Owner-checked POSIX Unix-domain control channel for the local model service.

This is an *additional* privileged control path, not a replacement for the
browser's bearer-authenticated HTTP routes. Linux verifies SO_PEERCRED;
macOS/BSD verifies getpeereid(). Unsupported platforms fail closed.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import socket
import socketserver
import stat
import struct
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

MAX_CONTROL_BYTES = 8192
SOCKET_NAME = "control.sock"


def control_path(data_dir: Path) -> Path:
    preferred = Path(data_dir).resolve() / "ipc" / SOCKET_NAME
    if len(os.fsencode(preferred)) <= 100:
        return preferred
    # macOS has a short sun_path limit; put an owner-only private directory
    # in /tmp using a deterministic digest of the normal data directory.
    digest = hashlib.sha256(os.fsencode(Path(data_dir).resolve())).hexdigest()[:20]
    return Path("/tmp") / f"cortex-ipc-{os.geteuid()}-{digest}" / SOCKET_NAME


def _peer_uid(connection: socket.socket) -> int:
    if sys.platform.startswith("linux"):
        credentials = connection.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
        )
        _pid, uid, _gid = struct.unpack("3i", credentials)
        return uid
    if sys.platform == "darwin":
        # Python's socket wrapper does not expose getpeereid on every build;
        # query Apple's documented libc function and fail closed on error.
        function = ctypes.CDLL(None, use_errno=True).getpeereid
        function.argtypes = [
            ctypes.c_int, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)
        ]
        function.restype = ctypes.c_int
        uid, gid = ctypes.c_uint(), ctypes.c_uint()
        if function(connection.fileno(), ctypes.byref(uid), ctypes.byref(gid)):
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return uid.value
    raise OSError("Peer credentials not supported by this operating system")


def _secure_directory(path: Path) -> None:
    if path.is_symlink():
        raise PermissionError("IPC directory must not be a symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise PermissionError("IPC directory must belong to the current user")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise PermissionError("IPC directory must have mode 0700")


def _prepare_socket(path: Path) -> None:
    if len(os.fsencode(path)) > 100:
        raise ValueError("IPC socket path is too long for portable Unix sockets")
    _secure_directory(path.parent)
    if not path.is_symlink() and not path.exists():
        return
    info = path.lstat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.geteuid():
        raise PermissionError("Refusing to replace an untrusted IPC path")
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(0.5)
        probe.connect(str(path))
    except (ConnectionRefusedError, FileNotFoundError):
        # An orphaned socket is safe to reclaim inside the 0700 directory.
        path.unlink()
    else:
        raise RuntimeError("Another Cortex control server is already running")
    finally:
        probe.close()


class _UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    block_on_close = False
    allow_reuse_address = False


class _ControlHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        connection = self.request
        connection.settimeout(3.0)
        owner: OwnerControl = self.server.control  # type: ignore[attr-defined]
        try:
            uid = _peer_uid(connection)
            if uid != owner.owner_uid:
                owner._send(connection, {"ok": False, "error": "peer_denied"})
                return
            # readline(cap) prevents a peer from forcing unbounded memory usage.
            with connection.makefile("rb") as stream:
                line = stream.readline(MAX_CONTROL_BYTES + 1)
            if not line or len(line) > MAX_CONTROL_BYTES or not line.endswith(b"\n"):
                owner._send(connection, {"ok": False, "error": "request_too_large"})
                return
            try:
                request = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                owner._send(connection, {"ok": False, "error": "invalid_json"})
                return
            if not isinstance(request, dict):
                owner._send(connection, {"ok": False, "error": "invalid_request"})
                return
            kind = request.get("command")
            if kind == "status" and set(request) == {"command"}:
                owner._send(connection, {"ok": True, "data": owner.get_status()})
            elif (kind == "cancel" and set(request) == {"command", "id"}
                  and isinstance(request["id"], str)
                  and re.fullmatch(r"[0-9a-f]{32}", request["id"])):
                try:
                    cancelled = owner.cancel_job(request["id"])
                    owner._send(connection, {"ok": True, "cancelled": bool(cancelled)})
                except (KeyError, ValueError):
                    owner._send(connection, {"ok": False, "error": "job_not_found_or_running"})
            else:
                owner._send(connection, {"ok": False, "error": "unknown_command"})
        except (OSError, TimeoutError, BrokenPipeError):
            # The peer disconnected or sent an incomplete request.
            return


class OwnerControl:
    """An optional OS-verified management socket with no prompt payloads."""

    def __init__(
        self, data_dir: Path, get_status: Callable[[], dict[str, Any]],
        cancel_job: Callable[[str], bool],
    ) -> None:
        if os.name != "posix":
            raise NotImplementedError("POSIX Unix sockets only; Windows pipe pending")
        self.path = control_path(data_dir)
        self.owner_uid = os.geteuid()
        self.get_status = get_status
        self.cancel_job = cancel_job
        self._server: _UnixServer | None = None
        self._thread: threading.Thread | None = None

    @staticmethod
    def _send(peer: socket.socket, response: dict[str, Any]) -> None:
        payload = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
        if len(payload) > MAX_CONTROL_BYTES:
            payload = b'{"ok":false,"error":"response_too_large"}\n'
        peer.sendall(payload)

    def start(self) -> None:
        _prepare_socket(self.path)
        server = _UnixServer(str(self.path), _ControlHandler)
        os.chmod(self.path, 0o600)
        server.control = self  # type: ignore[attr-defined]
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever, daemon=True, name="cortex-owner-control"
        )
        self._thread.start()

    def close(self) -> None:
        server = self._server
        if server is None:
            return
        server.shutdown()
        server.server_close()
        self._server = None
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._thread = None
        if self.path.exists() and stat.S_ISSOCK(self.path.lstat().st_mode):
            self.path.unlink()


def request_control(data_dir: Path, command: str, experiment_id: str | None = None) -> dict:
    payload: dict[str, str] = {"command": command}
    if experiment_id:
        payload["id"] = experiment_id
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as peer:
        peer.settimeout(4)
        peer.connect(str(control_path(data_dir)))
        peer.sendall((json.dumps(payload) + "\n").encode())
        with peer.makefile("rb") as stream:
            response = stream.readline(MAX_CONTROL_BYTES + 1)
    if len(response) > MAX_CONTROL_BYTES:
        raise ValueError("Oversize local IPC response")
    result = json.loads(response)
    if not isinstance(result, dict):
        raise ValueError("Invalid local IPC response")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Owner-only local Cortex control")
    parser.add_argument("command", choices=["status", "cancel"])
    parser.add_argument("id", nargs="?")
    parser.add_argument("--data-dir", type=Path,
                        default=Path(os.environ.get(
                            "CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger")
                        )))
    args = parser.parse_args()
    if (args.command == "cancel") != (args.id is not None):
        parser.error("cancel needs an experiment id; status takes no id")
    response = request_control(args.data_dir, args.command, args.id)
    print(json.dumps(response, indent=2))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
