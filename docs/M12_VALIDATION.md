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
