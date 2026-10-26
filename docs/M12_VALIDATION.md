# M12 phase 1 validation — 2026-10-26 (Asia/Seoul)

## Verified scope

This is a **source-only development milestone** committed to `main`,
NOT a new signed or published M12 installer. The public
[v0.11.0-rc1 release](https://github.com/parksy1625/cortex-debugger/releases/tag/v0.11.0-rc1)
remains unchanged.

| Check | Source-backed result |
| --- | --- |
| Linux kernel SO_PEERCRED UID, socket permissions, malformed input, alternate process client and safe lifecycle | [M12 owner IPC workflow — Ubuntu](https://github.com/parksy1625/cortex-debugger/actions/runs/40264670817): **PASS** |
| Apple Silicon/macOS libc getpeereid checks with the same independent test suite | [M12 owner IPC workflow — macOS 15](https://github.com/parksy1625/cortex-debugger/actions/runs/40264670817): **PASS** |
| Python Ruff and full suite | [Quality run #40264670862](https://github.com/parksy1625/cortex-debugger/actions/runs/40264670862): **119 passed, 1 optional skipped**, Ruff clean |
| React compiled application | [Quality run #40264670862](https://github.com/parksy1625/cortex-debugger/actions/runs/40264670862): **PASS** |
| Owner IPC socket enabled alongside localhost API and real GPT-2 through Chromium | [M12 live API-browser run #40264670933](https://github.com/parksy1625/cortex-debugger/actions/runs/40264670933): **PASS** |
| Documentation-only final commit quality | [#40264772026](https://github.com/parksy1625/cortex-debugger/actions/runs/40264772026): **PASS** |

## New control channel

- The optional POSIX `OwnerControl` server is started and cleaned up in
  FastAPI lifespan if `CORTEX_OWNER_IPC=1`; `launchers/start.sh`
  enables it for future Linux/macOS source-based packaged launches.
- Uses OS-owned Unix socket with private 0700 parent and 0600 socket mode.
- Kernel peer UID must match the server user's effective UID; other peers
  are rejected. Linux uses SO_PEERCRED, macOS Apple libc getpeereid().
- Strict, bounded, one-message JSON-line `status` and `cancel` protocol.
  Read-only `status` excludes raw prompts. `cancel` requires 32 lowercase
  hexadecimal characters and delegates to existing cancellable-job checks.
- Robust behavior includes stale-socket detection/recovery, refusing to
  overwrite active listeners or path symlinks/files, a short-path fallback
  for macOS sun_path limits, and graceful close/unlink.
- Existing browser API keeps M11 one-time pairing + bearer verification.
  The owner socket is **not** the browser API transport yet.

## Security caveats and next acceptance gates

An attacker with the **same OS account/UID** can legitimately connect to
this socket. This protection separates OS user accounts, not programs or
processes sharing the same user. Root/admin users are outside this boundary.
The named-pipe equivalent with proper client identity validation and DACL
is **not implemented on Windows**; that platform still uses M11 bearer HTTP.

A hardened product should route sensitive operations through explicitly
authenticated local IPC, perform code signing/notarization under the owner's
certificate, complete GUI UX and native interactions, and verify packages
and model inference on all three platforms under a new M12 tag. The old
v0.11.0-rc1 assets were not modified.

## Phase 2 — Windows x64 named pipe (2026-10-26)

- [M12 Windows named-pipe CI #40296700666](https://github.com/parksy1625/cortex-debugger/actions/runs/40296700666):
  **7 Windows-native tests passed** on windows-2022, including SID checks,
  DACL, request bounds, separate process, second server rejection and
  FastAPI lifecycle.
- [Linux Python/Ruff/React #40296700609](https://github.com/parksy1625/cortex-debugger/actions/runs/40296700609):
  **119 passed, 8 skipped** (7 Windows-only tests and one optional
  real-model test), Ruff and web build successful.
- [Actual Linux GPT-2 API/Chromium regression #40296700598](https://github.com/parksy1625/cortex-debugger/actions/runs/40296700598):
  **PASS** with the new Windows code present.
- [Windows implementation and threat model](M12_WINDOWS_PIPE.md).

Windows client verification uses the kernel impersonation token's SID,
not a client-supplied claimed identity. The pipe rejects remote clients
and has an explicit current-user-only DACL. The tests inject an unrelated
SID into the server validation path, but **do not log on as a second
independent Windows user**; independent cross-account denial still requires
manual or controlled multi-login QA.

There is still **no new packaged M12 installer**, and browser model
operations continue to use the paired localhost HTTP channel. Do not
describe this separate named pipe as comprehensive application sandboxing.
