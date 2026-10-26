"""Check both launchers invalidate their setup marker for a changed wheel."""

from pathlib import Path

LAUNCHERS = Path(__file__).resolve().parents[1] / "launchers"
READY_MARKER = ".cortex-runtime-wheel-sha256"


def test_posix_setup_marker_is_content_based_and_written_after_install():
    source = (LAUNCHERS / "start.sh").read_text(encoding="utf-8")
    assert "hashlib.file_digest" in source
    assert READY_MARKER in source
    assert '"$(<"$READY_MARKER")" != "$WHEEL_SHA256"' in source
    assert source.index('pip install "${WHEEL}[ml,api]"') < source.index('mv -f "$READY_MARKER.tmp.$$"')
    assert ".cortex-m11-ready" not in source


def test_windows_setup_marker_is_content_based_and_written_after_install():
    source = (LAUNCHERS / "start.ps1").read_text(encoding="utf-8")
    assert "Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256" in source
    assert READY_MARKER in source
    assert "if ($installedSha256 -ne $wheelSha256)" in source
    assert source.index("Cortex dependency install failed") < source.index("Move-Item -LiteralPath")
    assert ".cortex-m11-ready" not in source
