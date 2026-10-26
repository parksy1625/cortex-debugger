"""Pure stdlib tests for the ZIP runtime verifier's trust boundaries."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.smoke_m12_candidate import extract_candidate, verify_checksum


class CandidateSmokeValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "Cortex-Debugger-v0.12.0-rc1.zip"
        self.sidecar = self.root / (self.archive.name + ".sha256")

    def _make_zip(self, extra=None):
        with ZipFile(self.archive, "w") as bundle:
            for name in [
                "start.sh", "start.ps1", "Start-Cortex.command",
                "runtime-preflight.py", "apps/api/main.py",
                "apps/api/owner_ipc.py", "apps/api/owner_pipe_windows.py",
                "apps/web/dist/index.html",
                "wheel/cortex_debugger-0.12.0rc1-py3-none-any.whl",
            ]:
                bundle.writestr(name, "dummy")
            bundle.writestr("README-RELEASE.md", "v0.12.0-rc1")
            if extra:
                for name, content in extra:
                    bundle.writestr(name, content)
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.sidecar.write_text(f"{digest}  {self.archive.name}\n", encoding="utf-8")

    def test_checksums_and_member_versions(self):
        self._make_zip()
        verify_checksum(self.archive, self.sidecar)
        wheel = extract_candidate(self.archive, self.root / "extracted")
        self.assertTrue(wheel.is_file())
        self.assertTrue((self.root / "extracted" / "apps/api/main.py").exists())

    def test_tampering_and_misnamed_sidecar_rejected(self):
        self._make_zip()
        self.sidecar.write_text("a" * 64 + "  other.zip\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sidecar"):
            verify_checksum(self.archive, self.sidecar)
        self.sidecar.write_text("0" * 64 + f"  {self.archive.name}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_checksum(self.archive, self.sidecar)

    def test_unsafe_archive_members_rejected_before_extraction(self):
        self._make_zip(extra=[("../outside.txt", "not safe")])
        with self.assertRaisesRegex(ValueError, "unsafe path"):
            extract_candidate(self.archive, self.root / "extracted")
        self.assertFalse((self.root / "outside.txt").exists())


if __name__ == "__main__":
    unittest.main()
