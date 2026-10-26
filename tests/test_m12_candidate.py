"""Small, model-free checks of M12 candidate ZIP version and immutability."""

from __future__ import annotations

import hashlib
from zipfile import ZipFile

import pytest

from scripts.build_release import build


def _fake_bundle_source(root, wheel_version="0.12.0rc1"):
    files = {
        "dist/cortex_debugger-" + wheel_version + "-py3-none-any.whl": "wheel",
        "apps/web/dist/index.html": "<div id='root'></div>",
        "apps/web/dist/assets/main.js": "console.log('ready')",
        "apps/api/main.py": "app = None",
        "launchers/start.sh": "#!/bin/sh",
        "launchers/start.ps1": "# pwsh",
        "scripts/runtime_preflight.py": "# preflight",
        "docs/M12_RELEASE.md": "# v0.12.0-rc1",
        "LICENSE": "MIT",
        "requirements-linux-py311.lock": "# lock",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_m12_candidate_has_matching_wheel_and_checksum(tmp_path):
    _fake_bundle_source(tmp_path)
    dest = tmp_path / "artifacts" / "Cortex-Debugger-v0.12.0-rc1.zip"
    result = build(tmp_path, dest, "v0.12.0-rc1")

    assert result["version"] == "v0.12.0-rc1"
    assert result["wheel"].startswith("cortex_debugger-0.12.0rc1-")
    assert result["sha256"] == hashlib.sha256(dest.read_bytes()).hexdigest()
    assert dest.with_suffix(".zip.sha256").read_text().startswith(result["sha256"])
    with ZipFile(dest) as archive:
        assert "README-RELEASE.md" in archive.namelist()
        assert b"v0.12.0-rc1" in archive.read("README-RELEASE.md")

    original = dest.read_bytes()
    with pytest.raises(FileExistsError):
        build(tmp_path, dest, "v0.12.0-rc1")
    assert dest.read_bytes() == original


def test_mismatched_or_invalid_version_cannot_build(tmp_path):
    _fake_bundle_source(tmp_path, wheel_version="0.11.0rc1")
    dest = tmp_path / "Cortex-Debugger-v0.12.0-rc1.zip"
    with pytest.raises(ValueError, match="does not match"):
        build(tmp_path, dest, "v0.12.0-rc1")
    with pytest.raises(ValueError, match="Release candidate version"):
        build(tmp_path, dest, "../../bad")
    with pytest.raises(ValueError, match="filename must match"):
        build(tmp_path, tmp_path / "wrong.zip", "v0.12.0-rc1")
    assert not dest.exists()
