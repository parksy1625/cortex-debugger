# M11 validated release — 2026-10-25 (Asia/Seoul)

## Scope

M11 provides per-launch **one-time desktop-browser pairing** and an
authenticated local HTTP API. The released v0.11.0-rc1 binaries are distinct
from the unchanged v0.10.0-rc1 packages. This is application-level
authorization, *not* OS peer-credential isolation.

## Continuous integration evidence

| Verification | GitHub Actions evidence | Result |
| --- | --- | --- |
| Python unit/API security cases (111 tests, 1 optional skipped) and Ruff + React production build | [#40168426785](https://github.com/parksy1625/cortex-debugger/actions/runs/40168426785) | PASS |
| Browser E2E including code entry, bearer request, sessionStorage behavior | [#40168267306](https://github.com/parksy1625/cortex-debugger/actions/runs/40168267306) | PASS |
| Actual GPT-2 behind paired local FastAPI/React developer stack | [#40168267293](https://github.com/parksy1625/cortex-debugger/actions/runs/40168267293) | PASS |
| Pinned GPT-2 regression validation | [#40168267303](https://github.com/parksy1625/cortex-debugger/actions/runs/40168267303) | PASS |
| Unpack **actual M11 runtime ZIP** into clean Linux environment, verify 401 without pairing, then pair in Chromium and execute real GPT-2 | [#40168267362](https://github.com/parksy1625/cortex-debugger/actions/runs/40168267362) | PASS |
| Apple Silicon Mac native Finder `.app` bootstrap + pairing + real MPS GPT-2, publish ZIP | [#40168426750](https://github.com/parksy1625/cortex-debugger/actions/runs/40168426750) | PASS |
| Independently install the published base ZIP on Apple MPS, pair and run GPT-2 | [#40168426683](https://github.com/parksy1625/cortex-debugger/actions/runs/40168426683) | PASS |
| Windows x64 public ZIP, PowerShell bootstrap, one-time pairing, real GPT-2 CPU and WinForms EXE integrity self-test; publish GUI ZIP | [#40168426711](https://github.com/parksy1625/cortex-debugger/actions/runs/40168426711) | PASS |

## Download tested assets

- [Mac Finder .app ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-macOS-App-v0.11.0-rc1.zip) (SHA-256: `34b7234c5f86d47c771c53006ec85e602f12b555492f4032bf4cd79ed43be461`)
- [Windows x64 GUI ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-Windows-v0.11.0-rc1.zip) (SHA-256: `c44b3a7dcf2911bddff9e47ecae2f7c1c05b9c4981d2a6ad15a2ab7fecb95659`)
- [Base bootstrap ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-v0.11.0-rc1.zip) (SHA-256: `f780144201fd87daeffc11bcd685f2b87dfbd9f7ca680688b55a573f56a89f53`)

Each ZIP is accompanied by a `.sha256` file on the
[release page](https://github.com/parksy1625/cortex-debugger/releases/tag/v0.11.0-rc1).

## Auth and threat model

- At startup, `start.sh` or `start.ps1` creates a cryptographically
  random nine-digit code. The native Windows GUI generates and shows one;
  the Mac Finder wrapper opens Terminal where the code is displayed.
- The server consumes its environment code at import time to reduce exposure
  to child model processes. Codes expire 10 minutes after backend initialization,
  permit eight attempts, and mint **one** 256-bit bearer capability.
- Authorization header required for all private `/api/v1/*` endpoints.
  Health/setup/auth status remain public but do not include secret tokens.
- The browser stores the bearer only in tab-scoped `sessionStorage`, not
  cookies, localStorage, URLs, experiment DB or downloads. Restart revokes it.

### What remains unprotected

A malicious process running as the **same OS user** can potentially obtain
the code from the launch process, inspect browser state, or interfere with
the loopback service. The code can also be locked by repeated invalid
attempts. Bearer token confidentiality depends on preventing same-origin
script injection; `sessionStorage` is accessible to first-party JavaScript.
Direct raw `uvicorn` developer mode without a configured pairing code
remains unauthenticated; it must never be exposed beyond loopback.

The Windows native GUI button interactions and Mac Finder double-click/UI
prompts have not been automated in CI, despite the successful actual
package startup and model-backed tests. Dependencies and GPT-2 weights are
not bundled; Python 3.11+ and first-use internet are required. Apps are
unsigned and Mac `.app` is not notarized. SHA-256 is an integrity check, not
a publisher signature. Full evidence/regression files may contain prompt
tokens or raw input; deleting an SQLite row is not secure filesystem erasure.

M12 should pursue **OS owner-verified Unix socket / Windows named pipe IPC**,
native GUI first-run handling, publisher code signatures and notarization.
