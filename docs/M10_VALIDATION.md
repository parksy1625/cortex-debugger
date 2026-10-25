# M10 validation — 2026-10-25 KST

## Verified published release

| Scope | GitHub Actions evidence | Status |
| --- | --- | --- |
| Linux Python/Ruff and React | [#40166418607](https://github.com/parksy1625/cortex-debugger/actions/runs/40166418607) — **105 Python tests passed; one optional real-model test skipped**; web build | PASS |
| Base ZIP: fresh unpack, local FastAPI and real React/GPT-2 Chromium | [#40166264559](https://github.com/parksy1625/cortex-debugger/actions/runs/40166264559) | PASS |
| Source-stack API/browser against actual GPT-2 | [#40166264547](https://github.com/parksy1625/cortex-debugger/actions/runs/40166264547) | PASS |
| Pinned GPT-2 regression replay | [#40166264589](https://github.com/parksy1625/cortex-debugger/actions/runs/40166264589) | PASS |
| Browser tests, including local readiness panel | [#40166264563](https://github.com/parksy1625/cortex-debugger/actions/runs/40166264563) | PASS |
| macOS Finder .app launcher, fresh dependency bootstrap, actual Apple MPS GPT-2 | [#40166418684](https://github.com/parksy1625/cortex-debugger/actions/runs/40166418684) | PASS |
| Published runtime ZIP on macOS MPS | [#40166479260](https://github.com/parksy1625/cortex-debugger/actions/runs/40166479260) | PASS |
| Windows public ZIP, PowerShell startup, actual CPU GPT-2, portable .NET GUI self-test | [#40166418604](https://github.com/parksy1625/cortex-debugger/actions/runs/40166418604) | PASS |

## Artifacts

- [Mac Finder launcher ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-macOS-App-v0.10.0-rc1.zip)
- [Windows portable GUI ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-Windows-v0.10.0-rc1.zip)
- [Base runtime ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-v0.10.0-rc1.zip)

Each ZIP is accompanied by its own SHA-256 checksum on the
[prerelease page](https://github.com/parksy1625/cortex-debugger/releases/tag/v0.10.0-rc1).
SHA-256 permits integrity checking but **does not** constitute
publisher authentication or code signing. The pre-existing v0.9 packages
were not overwritten.

## M10 engineering changes

1. API request middleware rejects nonloopback Host values, untrusted
   Origin and cross-site browser requests, with an explicit opt-in only for
   trusted Vite development origin at port 5173.
2. `GET /api/v1/setup` reports safe operating-system, runtime, dependency
   availability and disk capacity signals, without loading the model.
   React Studio now displays these in a responsive diagnostics panel.
3. Subprocess model output reading is limited to a 1 MiB JSON-line
   response. Oversize worker data terminates the child process; a
   malicious-output unit test verifies this rejection and cleanup.
4. Actual model regression checks and warm/cold model integration still
   pass the new boundary.

## Important boundaries

- This is **browser-oriented CSRF/DNS-rebinding defense, not true local
  authorization**. A malicious local process can spoof HTTP metadata and
  invoke the unauthenticated loopback API. Avoid hostile shared computers.
- Status `torch_installed` checks module availability but does not
  guarantee sufficient RAM or compatible MPS acceleration on other Macs.
- One MPS and Windows/CPU smoke sample does not establish universal hardware
  compatibility or exact numerical reproducibility.
- Native launchers are *not offline AI binaries*: first run requires Python
  3.11+, internet and model dependencies. No code signing or notarization.
- The native UI window/Finder graphical click path is not covered by these
  headless smoke tests. Mac launch executable and Windows GUI EXE self-test
  are covered.
- Raw regression exports include prompts; full evidence may include token
  IDs; SQLite deletion does not securely wipe historical backups/journal.
