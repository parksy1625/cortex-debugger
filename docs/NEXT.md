# M12 roadmap and verified scope

Phase 1 on main: Linux/macOS owner-verified Unix control IPC with strict
socket/parent modes, kernel peer credential verification, bounded JSON-line
status/cancel commands and lifespan cleanup. This is *not yet* a public
M12 binary or an OS-authenticated transport for every browser/API request.

1. Verify POSIX peer UID tests in both Ubuntu and Apple Silicon GitHub Actions.
2. Verify FastAPI + real GPT-2 Chromium smoke while the IPC socket is enabled.
3. Windows x64 named-pipe control with a current-user-only DACL and verified
   caller SID is implemented on main, with a separate Windows CI workflow.
   Confirm the latest workflow run before claiming release qualification.
4. Integrate authenticated local browser proxy safely with OS IPC, with
   a documented threat model for same-user attackers.
5. Improve first-install progress and error reporting, native GUI click QA,
   trust/signing/notarization and rollback; do not commit any signing keys.
6. After Linux, macOS and Windows packaged smoke pass, version and release
   v0.12.0 separately, never overwrite the existing v0.11.0-rc1 assets.
