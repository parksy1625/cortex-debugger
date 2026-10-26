"""Build a small, auditable local source/runtime bundle from vetted inputs.

Bundles the compiled UI, Python engine wheel, local API module, and start
scripts. Does NOT bundle Python itself, model weights, credentials or any
user-created experiment data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

VERSION = "v0.12.0-rc1"
ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^v(\d+\.\d+\.\d+)-rc(\d+)$")


def _add_file(archive: ZipFile, file: Path, name: str) -> None:
    if not file.is_file() or file.is_symlink():
        raise ValueError(f"Missing or unsupported bundle path: {file}")
    archive.write(file, name, compress_type=ZIP_DEFLATED)


def build(root: Path, output: Path, version: str = VERSION) -> dict:
    root = root.resolve()
    matched = VERSION_PATTERN.fullmatch(version)
    if matched is None:
        raise ValueError("Release candidate version must look like v0.12.0-rc1")
    if output.name != f"Cortex-Debugger-{version}.zip":
        raise ValueError("Release ZIP filename must match the requested version")
    dist = root / "apps" / "web" / "dist"
    wheels = sorted((root / "dist").glob("cortex_debugger-*.whl"))
    if len(wheels) != 1 or not (dist / "index.html").is_file():
        raise ValueError("Build Python wheel and web frontend before bundling")
    wheel_version = matched.group(1) + "rc" + matched.group(2)
    if not wheels[0].name.startswith(f"cortex_debugger-{wheel_version}-"):
        raise ValueError("Requested release version does not match the built Python wheel")
    if not (dist / "assets").is_dir():
        raise ValueError("Compiled frontend assets are missing")
    api = sorted((root / "apps" / "api").glob("*.py"))
    if not api or not any(p.name == "main.py" for p in api):
        raise ValueError("Local FastAPI modules are missing")
    milestone = matched.group(1).split(".")[1]
    release_notes = root / "docs" / f"M{milestone}_RELEASE.md"
    if not release_notes.is_file():
        raise ValueError(f"Missing release notes for {version}")
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or checksum.exists():
        raise FileExistsError("Release output already exists; use a fresh destination")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in [
            (root / "launchers" / "start.sh", "start.sh"),
            (root / "launchers" / "start.ps1", "start.ps1"),
            (root / "scripts" / "runtime_preflight.py", "runtime-preflight.py"),
            (release_notes, "README-RELEASE.md"),
            (root / "LICENSE", "LICENSE"),
            (root / "requirements-linux-py311.lock", "requirements-linux-py311.lock"),
            (wheels[0], f"wheel/{wheels[0].name}"),
        ]:
            _add_file(archive, source, name)
        for file in api:
            _add_file(archive, file, f"apps/api/{file.name}")
        for file in sorted(dist.rglob("*")):
            if file.is_file():
                _add_file(archive, file, f"apps/web/dist/{file.relative_to(dist).as_posix()}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {
        "file": str(output),
        "sha256": digest,
        "size_bytes": output.stat().st_size,
        "wheel": wheels[0].name,
        "version": version,
        "files": len(ZipFile(output).namelist()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    output = arguments.output or Path(f"artifacts/Cortex-Debugger-{arguments.version}.zip")
    print(json.dumps(build(ROOT, output, arguments.version), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
