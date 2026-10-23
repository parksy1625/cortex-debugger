"""M9 Finder .app wrapper packaging, tested without macOS dependencies."""
from __future__ import annotations

import plistlib
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.build_macos_app import build


def test_macos_app_includes_exact_published_runtime(tmp_path):
    runtime = tmp_path / "release.zip"
    with ZipFile(runtime, "w", ZIP_DEFLATED) as archive:
        archive.writestr("start.sh", "echo localhost")
        archive.writestr("start.ps1", "Write-Host 'localhost'")
        archive.writestr("README-RELEASE.md", "M8 bundle")
        archive.writestr("apps/web/dist/index.html", "<html/>")
        archive.writestr("wheel/cortex_debugger-0.9.0rc1-py3-none-any.whl", "dummy")
    app = build(runtime, tmp_path / "out")
    assert app.name == "Cortex Debugger.app"
    binary = app / "Contents" / "MacOS" / "CortexDebugger"
    assert binary.is_file()
    assert binary.stat().st_mode & 0o111
    source = binary.read_text()
    assert "CORTEX_TEST_LAUNCH" in source
    assert "Library/Application Support/Cortex Debugger" in source
    assert "127.0.0.1:8000" in source
    assert (app / "Contents/Resources/runtime/start.sh").read_text() == "echo localhost"
    with (app / "Contents/Info.plist").open("rb") as fp:
        plist = plistlib.load(fp)
    assert plist["CFBundleExecutable"] == "CortexDebugger"
    assert plist["CFBundleIdentifier"] == "dev.cortexdebugger.local"


def test_rejects_invalid_zip_or_existing_app(tmp_path):
    incomplete = tmp_path / "bad.zip"
    with ZipFile(incomplete, "w") as archive:
        archive.writestr("start.sh", "bad")
    with pytest.raises(ValueError, match="unexpected or incomplete"):
        build(incomplete, tmp_path / "out")
    with ZipFile(incomplete, "w") as archive:
        for name in ("start.sh", "start.ps1", "README-RELEASE.md"):
            archive.writestr(name, "safe")
    build(incomplete, tmp_path / "out")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        build(incomplete, tmp_path / "out")


def test_rejects_path_traversal_in_release_zip(tmp_path):
    danger = tmp_path / "traverse.zip"
    with ZipFile(danger, "w") as archive:
        for name in ("start.sh", "start.ps1", "README-RELEASE.md"):
            archive.writestr(name, "data")
        archive.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError, match="Unsafe ZIP"):
        build(danger, tmp_path / "out")
