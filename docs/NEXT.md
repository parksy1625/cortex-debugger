# After M11: authenticated local model workbench

Completed: v0.11.0-rc1 published with real-model tests through a
one-time pairing code and per-process bearer token on Linux, Apple MPS,
and Windows CPU. Browser Host/Origin/Fetch-Site guards remain enabled.

1. OS-verified **owner-bound local IPC**: Unix socket peer credentials
   on macOS/Linux, Windows named-pipe peer identity and strict ACLs.
   Browser pairing is application-level auth, not an OS trust boundary.
2. GUI onboarding: more accurate model-download progress, capacity
   estimates, first-use cancellation and installation troubleshooting.
3. Native Windows GUI click tests / macOS Finder LaunchServices GUI tests;
   current CI uses headless launcher executable smoke.
4. Code signing, macOS notarization, verified release attestations,
   update channels and rollback; requires owner-managed credentials.
5. Avoid spawning user-editable interpreters or loading untrusted model
   checkpoint code without sandboxing; hard memory budgeting.
6. Better model backends and scientific evaluation beyond the pinned
   GPT-2 activation intervention once regression suites are ready.
