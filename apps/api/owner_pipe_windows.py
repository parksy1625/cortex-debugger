"""Windows owner-verified named-pipe control endpoint (M12 phase 2).

Named pipe DACL grants the current logon user only; every request is checked
again against the kernel client *impersonation token's* User SID.
This is a separate desktop control path; browsers retain M11 bearer HTTP.
Requires pywin32 on Windows. Not a same-user process isolation boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

MAX_CONTROL_BYTES = 8192
PIPE_REJECT_REMOTE_CLIENTS = 0x00000008
FILE_FLAG_FIRST_PIPE_INSTANCE = 0x00080000  # Win32 CreateNamedPipeW open mode
SECURITY_IDENTIFICATION = 0x00010000  # SECURITY_IMPERSONATION_LEVEL in CreateFileW


def _win32():
    if sys.platform != "win32":
        raise NotImplementedError("Windows named pipes are only available on Windows")
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32pipe
    import win32security

    return pywintypes, win32api, win32con, win32file, win32pipe, win32security


def _owner_sid():
    _, win32api, _, _, _, win32security = _win32()
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
    try:
        return win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    finally:
        token.Close()


def pipe_name(data_dir: Path) -> str:
    _, _, _, _, _, win32security = _win32()
    owner = win32security.ConvertSidToStringSid(_owner_sid())
    suffix = hashlib.sha256(
        (owner + "|" + os.path.normcase(str(Path(data_dir).absolute()))).encode("utf-8")
    ).hexdigest()[:24]
    return "\\\\.\\pipe\\cortex-owner-" + suffix


def _security_attributes():
    pywintypes, _, win32con, _, _, win32security = _win32()
    sid = _owner_sid()
    acl = win32security.ACL()
    acl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.GENERIC_ALL, sid)
    descriptor = win32security.SECURITY_DESCRIPTOR()
    descriptor.SetSecurityDescriptorOwner(sid, False)
    descriptor.SetSecurityDescriptorDacl(True, acl, False)
    attributes = pywintypes.SECURITY_ATTRIBUTES()
    attributes.SECURITY_DESCRIPTOR = descriptor
    attributes.bInheritHandle = False
    return attributes


def _client_sid(handle):
    _, win32api, _, _, _, win32security = _win32()
    # Always fail closed if impersonation or token acquisition fails.
    win32security.ImpersonateNamedPipeClient(handle)
    try:
        token = win32security.OpenThreadToken(
            win32api.GetCurrentThread(), win32security.TOKEN_QUERY, True
        )
        try:
            sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
            return win32security.ConvertSidToStringSid(sid)
        finally:
            token.Close()
    finally:
        # RevertToSelf is mandatory even when token inspection raises.
        win32security.RevertToSelf()


def _read_request(pipe):
    pywintypes, _, _, win32file, _, _ = _win32()
    # Message-mode read returns ERROR_MORE_DATA when the request is too large.
    try:
        _status, data = win32file.ReadFile(pipe, MAX_CONTROL_BYTES + 1)
    except pywintypes.error as exc:
        if exc.winerror == 234:
            return None
        raise
    if len(data) > MAX_CONTROL_BYTES or not data.endswith(b"\n"):
        return None
    try:
        value = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_response(pipe, response: dict[str, Any]) -> None:
    _, _, _, win32file, _, _ = _win32()
    payload = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
    if len(payload) > MAX_CONTROL_BYTES:
        payload = b'{"ok":false,"error":"response_too_large"}\n'
    win32file.WriteFile(pipe, payload)


class WindowsOwnerControl:
    """One server pipe instance held open for the full application lifespan."""

    def __init__(
        self, data_dir: Path, get_status: Callable[[], dict[str, Any]],
        cancel_job: Callable[[str], bool],
    ) -> None:
        if sys.platform != "win32":
            raise NotImplementedError("Windows only")
        self.name = pipe_name(data_dir)
        _, _, _, _, _, security = _win32()
        self.owner_sid = security.ConvertSidToStringSid(_owner_sid())
        self.get_status = get_status
        self.cancel_job = cancel_job
        self._stopping = threading.Event()
        self._thread: threading.Thread | None = None
        self._handle = None

    def start(self) -> None:
        if self._handle is not None:
            raise RuntimeError("Owner pipe already started")
        _, _, win32con, _, win32pipe, _ = _win32()
        self._handle = win32pipe.CreateNamedPipe(
            self.name,
            win32pipe.PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE,
            (win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE
             | win32pipe.PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS),
            1, MAX_CONTROL_BYTES, MAX_CONTROL_BYTES, 0, _security_attributes(),
        )
        self._thread = threading.Thread(target=self._serve, daemon=True, name="cortex-win-owner")
        self._thread.start()

    def _dispatch(self, request: dict[str, Any] | None) -> dict[str, Any]:
        if request is None:
            return {"ok": False, "error": "bad_or_oversized_request"}
        command = request.get("command")
        if command == "status" and set(request) == {"command"}:
            return {"ok": True, "data": self.get_status()}
        if (command == "cancel" and set(request) == {"command", "id"}
                and isinstance(request["id"], str)
                and re.fullmatch(r"[0-9a-f]{32}", request["id"])):
            try:
                return {"ok": True, "cancelled": bool(self.cancel_job(request["id"]))}
            except (KeyError, ValueError):
                return {"ok": False, "error": "job_not_found_or_running"}
        return {"ok": False, "error": "unknown_command"}

    def _serve(self) -> None:
        pywintypes, _, _, _, win32pipe, _ = _win32()
        handle = self._handle
        while not self._stopping.is_set():
            try:
                try:
                    win32pipe.ConnectNamedPipe(handle, None)
                except pywintypes.error as exc:
                    if exc.winerror != 535:  # ERROR_PIPE_CONNECTED
                        raise
                # Impersonation is valid only *after* receiving a message.
                message = _read_request(handle)
                if self._stopping.is_set():
                    break
                try:
                    if _client_sid(handle) != self.owner_sid:
                        _write_response(handle, {"ok": False, "error": "peer_denied"})
                    else:
                        _write_response(handle, self._dispatch(message))
                except (OSError, pywintypes.error, AttributeError):
                    # No command is dispatched if peer impersonation fails.
                    # Do not echo exception details that might include paths.
                    try:
                        _write_response(handle, {"ok": False, "error": "peer_auth_failed"})
                    except (OSError, pywintypes.error):
                        pass
            except (OSError, pywintypes.error):
                if self._stopping.is_set():
                    break
            finally:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                except pywintypes.error:
                    pass

    def close(self) -> None:
        handle = self._handle
        if handle is None:
            return
        self._stopping.set()
        # Stop does not wait for a reply: once the stop flag is set the
        # server intentionally closes the next client connection.
        try:
            _, _, win32con, win32file, _, _ = _win32()
            wake = win32file.CreateFile(
                self.name, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                0, None, win32con.OPEN_EXISTING,
                win32con.SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION, None,
            )
            try:
                win32file.WriteFile(wake, b'{"command":"status"}\n')
            finally:
                wake.Close()
        except (OSError, RuntimeError):
            pass
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                # Closing an active pipe handle underneath the service thread
                # can race with ReadFile/DisconnectNamedPipe. Keep ownership of
                # the handle and report an incomplete shutdown instead.
                raise RuntimeError("Owner pipe worker did not stop")
        handle.Close()
        self._handle = None
        self._thread = None


def request_control_name(name: str, payload: dict[str, str]) -> dict:
    pywintypes, _, win32con, win32file, win32pipe, _ = _win32()
    encoded = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_CONTROL_BYTES:
        raise ValueError("Oversize named-pipe request")
    try:
        client = win32file.CreateFile(
            name,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0, None, win32con.OPEN_EXISTING,
            win32con.SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION,
            None,
        )
    except pywintypes.error as exc:
        if exc.winerror != 231:  # ERROR_PIPE_BUSY between two sequential calls
            raise
        win32pipe.WaitNamedPipe(name, 4000)
        client = win32file.CreateFile(
            name,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0, None, win32con.OPEN_EXISTING,
            win32con.SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION,
            None,
        )
    try:
        win32file.WriteFile(client, encoded)
        _, response = win32file.ReadFile(client, MAX_CONTROL_BYTES + 1)
    finally:
        client.Close()
    if len(response) > MAX_CONTROL_BYTES or not response.endswith(b"\n"):
        raise ValueError("Invalid named-pipe response framing")
    result = json.loads(response)
    if not isinstance(result, dict):
        raise ValueError("Invalid named-pipe response")
    return result


def request_control(data_dir: Path, command: str, experiment_id: str | None = None) -> dict:
    payload = {"command": command}
    if experiment_id is not None:
        payload["id"] = experiment_id
    return request_control_name(pipe_name(data_dir), payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Windows owner-only Cortex pipe control")
    parser.add_argument("command", choices=["status", "cancel"])
    parser.add_argument("id", nargs="?")
    parser.add_argument("--data-dir", type=Path, default=Path(
        os.environ.get("CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger"))
    ))
    args = parser.parse_args()
    if (args.command == "cancel") != (args.id is not None):
        parser.error("cancel needs an experiment ID; status takes no ID")
    result = request_control(args.data_dir, args.command, args.id)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
