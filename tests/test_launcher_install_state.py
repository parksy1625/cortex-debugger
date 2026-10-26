"""Check both launchers invalidate their setup marker for a changed wheel."""

from pathlib import Path

LAUNCHERS = Path(__file__).resolve().parents[1] / "launchers"
READY_MARKER = ".cortex-runtime-wheel-sha256"


def test_posix_setup_marker_is_content_based_and_written_after_install():
    source = (LAUNCHERS / "start.sh").read_text(encoding="utf-8")
    assert "hashlib.file_digest" in source
    assert source.index('"$ROOT/runtime-preflight.py"') < source.index('"$PYTHON" -m venv')
    assert READY_MARKER in source
    assert '"$(<"$READY_MARKER")" != "$WHEEL_SHA256"' in source
    assert source.index('"$ROOT/runtime-preflight.py" --check-port') < source.index('"$PYTHON" -m venv')
    assert source.index('pip install "${WHEEL}[ml,api]"') < source.index('mv -f "$READY_MARKER.tmp.$$"')
    assert ".cortex-m11-ready" not in source


def test_windows_setup_marker_is_content_based_and_written_after_install():
    source = (LAUNCHERS / "start.ps1").read_text(encoding="utf-8")
    assert "Arguments = @('-3.11')" in source
    assert "Arguments = @('-3.12')" in source
    assert "Arguments = @('-3.13')" in source
    assert "Arguments = @('-3')" not in source
    assert "Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256" in source
    assert source.index("'runtime-preflight.py'") < source.index("-m venv")
    assert source.index("[Console]::IsOutputRedirected") < source.index("-m venv")
    assert source.index("'runtime-preflight.py') --check-port") < source.index("-m venv")
    assert "RandomNumberGenerator]::GetInt32" not in source
    assert "secrets.randbelow(1000000000)" in source
    assert READY_MARKER in source
    assert "if ($installedSha256 -ne $wheelSha256)" in source
    assert source.index("Cortex dependency install failed") < source.index("Move-Item -LiteralPath")
    assert ".cortex-m11-ready" not in source
