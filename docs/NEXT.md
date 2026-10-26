# M12 after Phase 2

Completed on main:
- Linux and macOS Unix-domain socket with owner UID verification.
- Windows x64 named-pipe control with explicit user SID DACL,
  remote-client rejection, request-time impersonated token SID checks.
- Both have only `status` and `cancel` commands, 8192-byte input ceiling.
- M11 browser bearer pairing and loopback-only HTTP are still separate.
- Native Windows pipe suite: 7 passed; Linux quality: 119 passed, 8 skipped
  (including 7 Windows-only tests), Chromium real GPT-2 integration passed.

Candidate work on PR #10 (not merged or published):
- Source version `0.12.0rc1`, isolated wheel/UI/ZIP packaging and a no-network
  preflight available through both native launchers.
- Linux extracted-ZIP install/API/pairing/owner-IPC smoke passed locally.
- GitHub Actions run #40333501723 passed Ubuntu/macOS/Windows extracted-ZIP
  smoke plus a real GPT-2 Chromium gate on the PR candidate source.
- Windows owner IPC run #40335189694 passed real denial by a disposable
  second local-account token, in addition to the native pipe protocol suite.
- M11 published artifacts are immutable; no M12 Release has been created.

Remaining milestones:
1. Manually validate Windows and Apple Silicon GUI click-through, setup,
   model loading and recovery on the actual extracted source runtime.
2. Consolidate IPC dispatch and probe denial/reconnect across truly separate
   interactive Windows sessions, beyond CI thread-token impersonation.
3. Decide whether to restrict sensitive model/job operations to an
   authenticated OS IPC proxy, without breaking the browser session.
4. Improve desktop first-run setup progress and GUI click test automation.
5. Add vetted native dependency locks, publisher signatures/notarization
   and rollback only when owner-controlled credentials are available.
6. Strengthen resource caps and default report privacy policy.
