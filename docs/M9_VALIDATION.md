# M9 measured release validation — 2026-10-24 KST

## Deliverables published on GitHub Releases

| Platform | Asset | Verification |
| --- | --- | --- |
| Mac Apple Silicon | [Cortex-Debugger-macOS-App-v0.9.0-rc1.zip](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-macOS-App-v0.9.0-rc1.zip) | [macOS app run #40015722520](https://github.com/parksy1625/cortex-debugger/actions/runs/40015722520): success, real MPS GPT-2 |
| Windows x64 | [Cortex-Debugger-Windows-v0.9.0-rc1.zip](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-Windows-v0.9.0-rc1.zip) | [Windows native run #40016740044](https://github.com/parksy1625/cortex-debugger/actions/runs/40016740044): success, real CPU GPT-2, GUI compiler and EXE self-test |
| Cross-platform baseline | [Original local runtime ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-v0.9.0-rc1.zip) | [M8 Linux packaged browser model test #40011290473](https://github.com/parksy1625/cortex-debugger/actions/runs/40011290473): success |

The Linux, macOS, and Windows launch paths were verified separately using a
pinned GPT-2 checkpoint `607a30d783dfa663caf39e06633721c8d4cfcd7e`.

## What is actually tested

### macOS

- A genuine Apple Silicon macOS runner downloaded the published runtime
  release and verified its SHA-256 checksum.
- Built an unsigned `Cortex Debugger.app` Finder bundle containing that
  runtime and a launcher executable.
- Called the packaged launcher with `CORTEX_TEST_LAUNCH=1`. It copied
  the runtime into a writable, user-scoped Application Support folder,
  installed native Python packages and booted the local web/API server.
- Confirmed MPS support, real pinned GPT-2 activation patching and matching
  revision/identity control.
- Published the tested `.app` ZIP and checksum as release assets.

The CI test did not automate Finder double-click, AppleScript Terminal
window activation or Gatekeeper prompts. The .app is **not** signed or notarized.

### Windows

- A Windows x64 runner downloaded the public `v0.9.0-rc1` runtime ZIP,
  verified its SHA-256 checksum, and extracted it.
- Launched `start.ps1`, installed Python/Torch/TransformerLens in a local
  virtual environment and booted `127.0.0.1:8000`.
- Performed real pinned GPT-2 CPU patching through the released HTTP API;
  it passed numeric identity and recovery checks.
- Built a .NET 8 self-contained, single-file Windows Forms GUI launcher,
  `CortexDebugger.exe`. This binary was copied into a **freshly extracted**
  runtime bundle and run with a headless `--self-test` validating the
  accompanying `start.ps1` and compiled UI files.
- Published a portable ZIP containing both EXE and runtime alongside a
  SHA-256 checksum.

The GUI itself is not a bundled Python executable: Python 3.11+ and internet
are still required for the first setup. Window button interactions have
not been automated and the executable is **not code-signed**.

## Security, provenance and remaining gaps

Release checksums verify asset bytes, but they do not replace a trusted
publisher signature or macOS notarization. GitHub Actions has recorded
passing build/test jobs and controls publication via `needs:`.

The API binds only to localhost and has no authentication; it should not
be exposed on a network or used on a hostile multi-user machine.
Experimental prompts can be recovered from raw token-ID evidence, and
regression JSON manifests include literal prompts. SQLite logical deletion
does not securely erase backups, journal pages or filesystem snapshots.

Next priority: production-grade signed installers, user-facing startup and
first-download progress UI, real GUI-click e2e and robust local API
authorization.
