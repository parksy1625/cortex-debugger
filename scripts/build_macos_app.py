"""Construct an unsigned native macOS .app *launcher* around the verified ZIP.

The .app is a Finder/LaunchServices wrapper. Python runtime and GPT-2 model
weights are downloaded on first run, NOT bundled. Runtime is copied outside
the read-only application bundle to Application Support before installation.
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
from pathlib import Path
from zipfile import ZipFile

NAME = "Cortex Debugger.app"
VERSION = "0.9.0rc1"

LAUNCHER = r'''#!/bin/bash
set -euo pipefail
CONTENTS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOURCE_DIR="$CONTENTS/Resources/runtime"
BASE="${CORTEX_RUNTIME_HOME:-$HOME/Library/Application Support/Cortex Debugger}"
WORK_DIR="$BASE/v0.9.0-rc1"
if [[ ! -f "$WORK_DIR/start.sh" ]]; then
    mkdir -p "$WORK_DIR"
    /usr/bin/ditto "$RESOURCE_DIR" "$WORK_DIR"
fi
if [[ "${CORTEX_TEST_LAUNCH:-0}" == "1" ]]; then
    cd "$WORK_DIR"
    exec /bin/bash "$WORK_DIR/start.sh"
fi
/usr/bin/osascript - "$WORK_DIR" <<'OSA'
on run argv
    set runtimeDir to item 1 of argv
    set terminalCommand to "cd " & quoted form of runtimeDir & "; (for n in $(seq 1 120); do if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then open http://127.0.0.1:8000/; break; fi; sleep 2; done) & /bin/bash ./start.sh"
    tell application "Terminal"
        activate
        do script terminalCommand
    end tell
end run
OSA
'''


def build(package_zip: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    app = destination / NAME
    if app.exists():
        raise ValueError(f"Refusing to overwrite existing app: {app}")
    macos = app / "Contents" / "MacOS"
    resources = app / "Contents" / "Resources"
    runtime = resources / "runtime"
    # Preflight the entire archive before touching the filesystem. An invalid
    # ZIP must not leave a half-created app that blocks a later safe attempt.
    with ZipFile(package_zip) as z:
        members = z.namelist()
        if not {"start.sh", "start.ps1", "README-RELEASE.md"}.issubset(members):
            raise ValueError("Cannot package an unexpected or incomplete runtime ZIP")
        for member in z.infolist():
            target = runtime / member.filename
            if not target.resolve().is_relative_to(runtime.resolve()):
                raise ValueError("Unsafe ZIP entry")
        macos.mkdir(parents=True)
        runtime.mkdir(parents=True)
        for member in z.infolist():
            target = runtime / member.filename
            if member.filename.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    binary = macos / "CortexDebugger"
    binary.write_text(LAUNCHER, encoding="utf-8")
    os.chmod(binary, 0o755)
    plist = {
        "CFBundleName": "Cortex Debugger",
        "CFBundleDisplayName": "Cortex Debugger",
        "CFBundleIdentifier": "dev.cortexdebugger.local",
        "CFBundleVersion": "0.9.0.1",
        "CFBundleShortVersionString": "0.9.0",
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "CortexDebugger",
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
    }
    with (app / "Contents" / "Info.plist").open("wb") as fp:
        plistlib.dump(plist, fp)
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    print(build(args.zip, args.out))
