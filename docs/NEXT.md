# After M8

1. Verify the produced ZIP on a fresh Linux runner: install its engine wheel
   in a clean venv, serve packaged static UI + local API on port 8000, and
   complete real GPT-2 Chromium end-to-end test.
2. Add separate macOS Apple Silicon and Windows bundle smoke workflows, and
   native environment lockfile validation.
3. Publish a v0.9.0-rc1 GitHub Release from a tag only after package smoke
   tests pass. Sign or attest release assets and document SHA-256 validation.
4. Improve prompt/token privacy, platform-native installers and notarization.
5. Make model loading/cancellation progress user friendly; profile peak
   memory and cold/warm startup across hardware.
6. Introduce a limited IPC response byte ceiling and OS memory cgroups/jobs.
7. Expand beyond GPT-2 only after adapter-level scientific tests.
