# M12 after Phase 2

Completed on main:
- Linux and macOS Unix-domain socket with owner UID verification.
- Windows x64 named-pipe control with explicit user SID DACL,
  remote-client rejection, request-time impersonated token SID checks.
- Both have only `status` and `cancel` commands, 8192-byte input ceiling.
- M11 browser bearer pairing and loopback-only HTTP are still separate.
- Native Windows pipe suite: 7 passed; Linux quality: 119 passed, 8 skipped
  (including 7 Windows-only tests), Chromium real GPT-2 integration passed.

Remaining milestones:
1. Consolidate IPC dispatch and probe real cross-user Windows denial in a
   controlled multi-account test environment; add denial/reconnect tests.
2. Decide whether to restrict sensitive model/job operations to an
   authenticated OS IPC proxy, without breaking the browser session.
3. Improve desktop first-run setup progress and GUI click test automation.
4. Create v0.12.0 release candidate and test actual extracted ZIP and
   Mac/Windows native GUI launchers with real GPT-2.
5. Add vetted native dependency locks, publisher signatures/notarization
   and rollback only when owner-controlled credentials are available.
6. Strengthen resource caps and default report privacy policy.
