"""Dependency-free preflight shared by M12 ZIP launchers on all operating systems.

Copy this script to ``runtime-preflight.py`` at the root of the source ZIP.
It never downloads packages, starts a service, or reads user experiments.
"""

from __future__ import annotations

import sys
from pathlib import Path

WHEEL_VERSION = "0.12.0rc1"


def validate(root: Path, *, python_version: tuple[int, int] | None = None) -> Path:
    """Return the sole compatible wheel; fail early on incomplete/old runtimes."""
    version = python_version if python_version is not None else sys.version_info[:2]
    if not (3, 11) <= version <= (3, 13):
        raise ValueError("Cortex Debugger M12 requires Python 3.11-3.13 for PyTorch 2.7")
    wheel_dir = root / "wheel"
    wheels = sorted(wheel_dir.glob("cortex_debugger-*.whl"))
    if (len(wheels) != 1 or not wheels[0].is_file() or wheels[0].is_symlink()
            or not wheels[0].name.startswith(f"cortex_debugger-{WHEEL_VERSION}-")):
        raise ValueError(f"Expected exactly one cortex_debugger-{WHEEL_VERSION} wheel")
    required = [
        "start.sh", "start.ps1", "README-RELEASE.md",
        "requirements-linux-py311.lock", "apps/api/main.py",
        "apps/api/owner_ipc.py", "apps/api/owner_pipe_windows.py",
        "apps/web/dist/index.html",
    ]
    for relative in required:
        file = root / relative
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"Candidate ZIP is missing a runtime file: {relative}")
    assets = root / "apps/web/dist/assets"
    if not assets.is_dir() or not any(path.is_file() for path in assets.iterdir()):
        raise ValueError("Candidate ZIP is missing the compiled web assets")
    return wheels[0]


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        wheel = validate(root)
    except ValueError as exc:
        print(f"Cortex M12 preflight failed: {exc}", file=sys.stderr)
        return 2
    print(f"Cortex M12 preflight OK: Python {sys.version_info.major}.{sys.version_info.minor}, {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
