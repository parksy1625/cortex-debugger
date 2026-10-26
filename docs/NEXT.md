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
- GitHub Actions now defines Ubuntu/macOS/Windows extracted-ZIP smoke plus a
  real GPT-2 Chromium gate, but those PR-head jobs have not run yet.
- M11 published artifacts are immutable; no M12 Release has been created.

Remaining milestones:
1. Trigger and validate PR #10's native Windows/Ubuntu/macOS candidate checks
   and real GPT-2 browser job before merging or publishing any M12 artifacts.
2. Consolidate IPC dispatch and probe real cross-user Windows denial in a
   controlled multi-account test environment; add denial/reconnect tests.
3. Decide whether to restrict sensitive model/job operations to an
   authenticated OS IPC proxy, without breaking the browser session.
4. Improve desktop first-run setup progress and GUI click test automation.
5. Test Mac/Windows native GUI launchers with real GPT-2 on the exact candidate.
6. Add vetted native dependency locks, publisher signatures/notarization
   and rollback only when owner-controlled credentials are available.
7. Strengthen resource caps and default report privacy policy.
