"""M12 runtime ZIP preflight: no downloads and no third-party dependencies."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.runtime_preflight import validate

SOURCE = Path(__file__).resolve().parents[1]


class RuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in [
            "wheel/cortex_debugger-0.12.0rc1-py3-none-any.whl",
            "README-RELEASE.md", "requirements-linux-py311.lock",
            "apps/api/main.py", "apps/api/owner_ipc.py",
            "apps/api/owner_pipe_windows.py", "apps/web/dist/index.html",
            "apps/web/dist/assets/main.js",
        ]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture", encoding="utf-8")
        for source, name in [
            (SOURCE / "launchers/start.sh", "start.sh"),
            (SOURCE / "launchers/start.ps1", "start.ps1"),
            (SOURCE / "scripts/runtime_preflight.py", "runtime-preflight.py"),
        ]:
            shutil.copyfile(source, self.root / name)

    def test_accepts_complete_bundle_and_supported_python(self):
        wheel = validate(self.root, python_version=(3, 11))
        self.assertEqual(wheel.parent.name, "wheel")
        self.assertEqual(wheel.name, "cortex_debugger-0.12.0rc1-py3-none-any.whl")

    def test_rejects_unsupported_python_and_mismatched_wheels(self):
        with self.assertRaisesRegex(ValueError, "Python 3.11"):
            validate(self.root, python_version=(3, 10))
        wheel = self.root / "wheel/cortex_debugger-0.12.0rc1-py3-none-any.whl"
        wheel.rename(self.root / "wheel/cortex_debugger-0.11.0rc1-py3-none-any.whl")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate(self.root, python_version=(3, 11))

    def test_missing_frontend_is_rejected(self):
        (self.root / "apps/web/dist/index.html").unlink()
        with self.assertRaisesRegex(ValueError, "index.html"):
            validate(self.root, python_version=(3, 11))

    @unittest.skipUnless(shutil.which("bash"), "Bash not installed")
    def test_posix_check_mode_does_not_install_or_launch(self):
        if __import__("os").name == "nt":
            self.skipTest("POSIX launcher not supported on Windows")
        result = subprocess.run(
            ["bash", str(self.root / "start.sh"), "--check"],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight OK", result.stdout)
        self.assertFalse((self.root / ".venv").exists())

    @unittest.skipUnless(shutil.which("bash"), "Bash not installed")
    def test_posix_noninteractive_launch_does_not_hide_pairing_code(self):
        if os.name == "nt":
            self.skipTest("POSIX launcher not supported on Windows")
        env = os.environ.copy()
        env.pop("CORTEX_PAIRING_CODE", None)
        result = subprocess.run(
            ["bash", str(self.root / "start.sh")], cwd=self.root,
            capture_output=True, text=True, env=env, timeout=15,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Cannot display a pairing code", result.stderr)
        self.assertFalse((self.root / ".venv").exists())

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell only")
    def test_windows_check_mode_skips_pairing_guard_and_install(self):
        env = os.environ.copy()
        env.pop("CORTEX_PAIRING_CODE", None)
        result = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(self.root / "start.ps1"), "-Check"],
            cwd=self.root, capture_output=True, text=True, env=env, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight OK", result.stdout)
        self.assertFalse((self.root / ".venv").exists())

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell only")
    def test_windows_redirected_launch_never_prints_secret_or_installs(self):
        env = os.environ.copy()
        env.pop("CORTEX_PAIRING_CODE", None)
        result = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(self.root / "start.ps1")],
            cwd=self.root, capture_output=True, text=True, env=env, timeout=20,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot display a pairing code", result.stdout + result.stderr)
        self.assertNotIn("Cortex pairing code:", result.stdout + result.stderr)
        self.assertFalse((self.root / ".venv").exists())


if __name__ == "__main__":
    unittest.main()
