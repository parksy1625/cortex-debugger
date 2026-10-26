"""Cross-platform, model-free smoke of the *extracted* M12 release candidate.

Run from a source checkout after downloading the unpublished Actions artifact.
The candidate wheel and API are installed and launched only from a fresh ZIP
extraction; source-tree imports cannot accidentally hide missing bundle files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import time
import venv
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

VERSION = "v0.12.0-rc1"
WHEEL_VERSION = "0.12.0rc1"
PAIRING_CODE = "123456789"  # Ephemeral CI fixture, never a user pairing code.


def verify_checksum(archive: Path, checksum: Path) -> None:
    """Verify the downloaded checksum sidecar before opening the ZIP."""
    line = checksum.read_text(encoding="utf-8").strip()
    expected_name = f"{archive.name}"
    parts = line.split("  ", 1)
    if (len(parts) != 2 or parts[1] != expected_name or len(parts[0]) != 64
            or any(char not in "0123456789abcdef" for char in parts[0])):
        raise ValueError("Invalid candidate SHA-256 sidecar")
    with archive.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != parts[0]:
        raise ValueError("Candidate ZIP SHA-256 does not match the sidecar")


def extract_candidate(archive: Path, destination: Path) -> Path:
    """Reject unsafe or mislabeled members before extracting the candidate."""
    if archive.name != f"Cortex-Debugger-{VERSION}.zip":
        raise ValueError("Unexpected candidate ZIP filename")
    with ZipFile(archive) as bundle:
        members = bundle.infolist()
        names = [entry.filename for entry in members]
        if len(names) != len(set(names)):
            raise ValueError("Candidate ZIP has duplicate entries")
        for entry in members:
            parts = entry.filename.split("/")
            if (entry.filename.startswith("/") or "\\" in entry.filename
                    or any(part in {"", ".", ".."} for part in parts)
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError("Candidate ZIP contains an unsafe path")
        required = {
            "start.sh", "start.ps1", "Start-Cortex.command",
            "runtime-preflight.py", "README-RELEASE.md",
            "apps/api/main.py", "apps/api/owner_ipc.py",
            "apps/api/owner_pipe_windows.py", "apps/web/dist/index.html",
        }
        if not required.issubset(names):
            raise ValueError("Candidate ZIP is missing runtime files")
        wheel_names = [name for name in names if name.startswith("wheel/") and name.endswith(".whl")]
        if len(wheel_names) != 1 or not wheel_names[0].startswith(
            f"wheel/cortex_debugger-{WHEEL_VERSION}-"
        ):
            raise ValueError("Candidate ZIP wheel version mismatch")
        if VERSION.encode() not in bundle.read("README-RELEASE.md"):
            raise ValueError("Candidate ZIP notes do not match its version")
        bundle.extractall(destination)
    return destination / wheel_names[0]


def _request(base: str, path: str, *, token: str = "", payload: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = Request(base + path, headers=headers, data=data)
    try:
        with urlopen(request, timeout=5) as response:
            content = response.read()
            return response.status, content
    except HTTPError as exc:
        return exc.code, exc.read()


def _port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _python(venv_directory: Path) -> Path:
    return (venv_directory / "Scripts" / "python.exe" if os.name == "nt"
            else venv_directory / "bin" / "python")


def smoke(extracted: Path, python: Path, data_dir: Path) -> None:
    port = _port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update({
        "CORTEX_OWNER_IPC": "1", "CORTEX_DATA_DIR": str(data_dir),
        "CORTEX_PAIRING_CODE": PAIRING_CODE,
        "PYTHONPATH": "",  # Never import the source checkout by accident.
    })
    log_path = extracted / "smoke-server.log"
    with log_path.open("wb") as output:
        process = subprocess.Popen(
            [str(python), "-m", "uvicorn", "apps.api.main:app",
             "--host", "127.0.0.1", "--port", str(port), "--workers", "1"],
            cwd=extracted, env=env, stdout=output, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Extracted candidate server exited during startup")
                try:
                    status, body = _request(base, "/api/v1/health")
                    if status == 200:
                        break
                except (OSError, TimeoutError):
                    pass
                time.sleep(0.25)
            else:
                raise TimeoutError("Extracted candidate did not become healthy")

            health = json.loads(body)
            assert health["stage"] == "M12" and health["version"] == WHEEL_VERSION
            assert health["local_only"] is True
            status, body = _request(base, "/")
            assert status == 200 and b'<div id="root"' in body
            status, body = _request(base, "/api/v1/auth/status")
            assert status == 200 and json.loads(body) == {
                "enabled": True, "authenticated": False
            }
            status, _ = _request(base, "/api/v1/models")
            assert status == 401, "Models endpoint must require browser pairing"

            status, body = _request(base, "/api/v1/auth/pair", payload={"code": PAIRING_CODE})
            assert status == 200
            token = json.loads(body)["token"]
            status, body = _request(base, "/api/v1/models", token=token)
            assert status == 200 and json.loads(body)["models"][0]["loaded"] is False
            status, _ = _request(base, "/api/v1/auth/pair", payload={"code": PAIRING_CODE})
            assert status == 403, "Pairing code must be single-use"

            module = ("apps.api.owner_pipe_windows" if os.name == "nt"
                      else "apps.api.owner_ipc")
            control = subprocess.run(
                [str(python), "-m", module, "status", "--data-dir", str(data_dir)],
                cwd=extracted, env=env, capture_output=True, text=True,
                timeout=15, check=True,
            )
            owner_status = json.loads(control.stdout)
            assert owner_status["ok"] is True
            assert owner_status["data"]["loaded"] is False
        except Exception:
            output.flush()
            # No pairing code is printed by uvicorn, but bound diagnostic size.
            print(log_path.read_text(errors="replace")[-2000:], file=sys.stderr)
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
    print(f"M12 extracted candidate PASS: {sys.platform}, {WHEEL_VERSION}, HTTP/pair/IPC")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checksum", type=Path, required=True)
    args = parser.parse_args()
    verify_checksum(args.archive, args.checksum)
    with tempfile.TemporaryDirectory(prefix="cortex-m12-zip-smoke-") as temp:
        root = Path(temp)
        extracted = root / "runtime"
        extracted.mkdir()
        wheel = extract_candidate(args.archive, extracted)
        launcher_check = (
            ["powershell", "-NoProfile", "-File", str(extracted / "start.ps1"), "-Check"]
            if os.name == "nt" else ["bash", str(extracted / "start.sh"), "--check"]
        )
        subprocess.run(launcher_check, cwd=extracted, check=True, timeout=20)
        if sys.platform == "darwin":
            # Exercise the Finder entry point's delegation to the actual
            # extracted launcher without making a GUI/Desktop claim.
            subprocess.run(
                ["bash", str(extracted / "Start-Cortex.command"), "--check"],
                cwd=extracted, check=True, timeout=20,
            )
        venv_directory = root / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_directory)
        python = _python(venv_directory)
        # The API/control-path smoke should not download PyTorch or model weights.
        subprocess.run(
            [str(python), "-m", "pip", "install", f"{wheel}[api]"],
            cwd=extracted, check=True, timeout=240,
        )
        smoke(extracted, python, root / "private-data")


if __name__ == "__main__":
    main()
