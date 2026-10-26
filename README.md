## M12 Phase 2: Windows SID-verified named pipe (development only)

M12 now provides **user-account-verified local control IPC on Linux, macOS
and Windows**. The Windows pipe uses an explicit current-user-only DACL,
remote-client rejection, request-time `ImpersonateNamedPipeClient` and
token SID verification. The only allowed owner controls are **model status**
and **cancel a validated experiment ID**. The Windows
[7-test native pipe suite](https://github.com/parksy1625/cortex-debugger/actions/runs/40296700666)
passed on a hosted Windows x64 runner.

This is **not protection from malicious processes running as the same user**
and does **not yet make browser HTTP calls use the pipe**. A real alternate
Windows account token was denied in CI, and extracted M12 ZIP API/browser
smoke has passed on Windows and Linux. Actual native GUI click-through,
separate logged-in desktop sessions, and Apple Silicon device validation
still require manual testing.

See [Windows IPC design](docs/M12_WINDOWS_PIPE.md) and the
[M12 verification log](docs/M12_VALIDATION.md).
The existing public v0.11.0-rc1 assets have not changed.

### M12 unpublished source-runtime candidate

The [M12 testing instructions](docs/M12_RELEASE.md) cover the Actions ZIP,
checksum verification, supported Python 3.11-3.13, and initial pairing. The
candidate now includes `Start-Cortex.command` for a visible macOS Finder-to-
Terminal launch. Windows PowerShell 5.1 uses Python's secure code generator;
both launchers check for local port 8000 conflicts and malformed supplied
pairing codes **before** dependency downloads. This is **not** a signed app,
offline installer, or published v0.12.0 release.

## M12 development: OS-verified owner control IPC (Linux and macOS)

**This is development on `main`, not a new downloadable release.**
The published v0.11.0-rc1 packages are unchanged.

The POSIX shell launch now starts an additional owner-only Unix socket
for model status and job cancellation. On Linux the kernel-reported UID
comes from `SO_PEERCRED`; on macOS from libc `getpeereid`.
A mode-0700 directory, mode-0600 socket, bounded JSON-line requests and
live-peer UID checks are enforced. Python CLI:

```bash
python -m apps.api.owner_ipc status
python -m apps.api.owner_ipc cancel 0123456789abcdef0123456789abcdef
```

The browser still uses M11 one-time pairing and bearer authorization over
loopback HTTP. **This does not move browser HTTP requests onto OS-authenticated
IPC**, and **same-account malware can use the socket** because it shares the
same UID. Windows named-pipe support has since landed on the M12 development
branch; independent candidate CI is in progress, with native desktop launch
still a manual gate. See [M12 architecture](docs/M12_OWNER_IPC.md).

## M11 v0.11.0-rc1 — one-time local browser pairing

**M11 is published and verified separately from v0.10.0-rc1.**
Download the model-tested builds:
[Mac Finder app](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-macOS-App-v0.11.0-rc1.zip),
[Windows GUI](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-Windows-v0.11.0-rc1.zip),
or [cross-platform ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.11.0-rc1/Cortex-Debugger-v0.11.0-rc1.zip).
See [M11 validation](docs/M11_VALIDATION.md).

The Windows and macOS bootstrap launchers now generate a nine-digit
one-time pairing code per launch. Users enter it in the local browser once
to obtain a random, process-scoped bearer token stored only in that browser
tab's `sessionStorage`. All non-public model/experiment API calls then
require the bearer token. Failed code attempts are capped; the code expires
after ten minutes and cannot be reused after successful pairing. Restarting
the application revokes the token.

The Windows native GUI displays a pairing code in its control panel.
macOS Terminal or standalone shell launch displays the code only when
attached to a terminal, not in redirected CI logs.

**Security scope:** this prevents unauthenticated API clients *without the
one-time code or bearer*. It cannot provide an operating-system boundary
against malicious software running under the same user. Such software can
inspect processes, launch environment or browser session memory. A dedicated
owner-bound named pipe/Unix socket remains future work.

Direct source developer launch via `uvicorn apps.api.main:app` remains in
an explicitly *unauthenticated compatibility mode* unless
`CORTEX_PAIRING_CODE` is configured before startup. Do not expose even
paired localhost HTTP services to a LAN/public network.

## M10 v0.10.0-rc1 — local browser protection and setup readiness

**v0.10.0-rc1 has now been published and model-validated on Linux, Apple Silicon macOS and Windows x64.** The previous v0.9.0-rc1 assets remain unchanged.

- Local API rejects non-loopback `Host` values and cross-site browser requests
  to reduce DNS-rebinding and malicious webpage request risks.
- Cross-site `Origin` (including `null`) is rejected. Same-origin browser
  calls and existing Python HTTP clients continue to work.
- Vite development uses an explicit opt-in `CORTEX_DEV_ORIGIN` for port 5173.
  The production compiled UI uses a single origin and needs no exception.
- The local Studio now exposes a **runtime readiness panel** reporting Python,
  installed PyTorch/TransformerLens, OS/architecture and approximate free
  disk space, without loading the AI model.
- These measures are **not local API authentication**. An untrusted process
  running under the same OS user can speak directly to the loopback service.
  Authenticated IPC and stronger local boundaries remain open research.

### M10 downloads (model-backed smoke verified)

- [macOS Apple Silicon Finder .app ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-macOS-App-v0.10.0-rc1.zip) — [Apple MPS app test](https://github.com/parksy1625/cortex-debugger/actions/runs/40166418684).
- [Windows x64 portable GUI .exe ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-Windows-v0.10.0-rc1.zip) — [native launcher plus CPU inference test](https://github.com/parksy1625/cortex-debugger/actions/runs/40166418604).
- [Python/web runtime bootstrap ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.10.0-rc1/Cortex-Debugger-v0.10.0-rc1.zip) — [extracted Linux/Chromium inference test](https://github.com/parksy1625/cortex-debugger/actions/runs/40166264559).

The Mac Finder launcher and Windows GUI are **not signed, notarized or
completely offline/self-contained**; Python 3.11+ and a network connection
are required on first setup. The native GUIs' manual interaction remains
unverified; only non-interactive launcher paths were exercised in CI.

For measurements and limitations see [M10 verification](docs/M10_VALIDATION.md).

Run M10 source in local development:

```bash
# In the server terminal, enable only the trusted Vite development origin:
CORTEX_DEV_ORIGIN=http://127.0.0.1:5173 python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
# In another terminal:
cd apps/web && npm ci && npm run dev
```

See [M10 security and setup notes](docs/M10_SECURITY_SETUP.md).

# Cortex Debugger

**Local-first activation-patching debugger, experiment studio and model regression gate.**

## M9 — Platform launchers (verified)

**macOS Apple Silicon:** [Download Finder .app ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-macOS-App-v0.9.0-rc1.zip). Extract the ZIP and launch `Cortex Debugger.app`. This unsigned Finder wrapper creates its writable runtime in Application Support and opens Terminal/browser. The [MPS packaged-app smoke test](https://github.com/parksy1625/cortex-debugger/actions/runs/40015722520) passed on GitHub macOS ARM64, but Finder double-click/AppleScript UI was not exercised automatically.

**Windows x64:** [Download Windows GUI ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-Windows-v0.9.0-rc1.zip). Extract the ZIP and open `CortexDebugger.exe`; the window offers Start, Stop and Open browser. The [native Windows test](https://github.com/parksy1625/cortex-debugger/actions/runs/40016740044) validated installation through PowerShell, real GPT-2 CPU inference, self-contained .NET GUI compilation and the packaged `--self-test` executable. Interactive window clicking was not automated.

**Both launchers require preinstalled Python 3.11+ and internet for first-run Python/model dependencies.** The Mac .app is unsigned/not notarized, and the Windows .exe is not code-signed. These are local launchers, not complete offline installers. See [M9 validation](docs/M9_VALIDATION.md).

## M8 · v0.9.0-rc1 (release candidate)

M8 adds a **downloadable local ZIP** with a compiled React web UI, the
Python `cortex_engine` wheel, API runtime modules and cross-platform
bootstrap scripts. Users no longer need Node or the Vite dev server to use
the bundled app after downloading. The runtime creates a Python virtualenv
and downloads dependencies and GPT-2 model weights on first launch.
This is a **bootstrap bundle, not a self-contained/offline binary**.

### Install the local bundle

1. Download the [v0.9.0-rc1 release ZIP](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-v0.9.0-rc1.zip) and optionally its [SHA-256 checksum](https://github.com/parksy1625/cortex-debugger/releases/download/v0.9.0-rc1/Cortex-Debugger-v0.9.0-rc1.zip.sha256).
2. **Unzip once** into a directory you own. The ZIP contains `start.sh`,
   `start.ps1`, the built UI, and a Python wheel.
3. On **macOS/Linux** run `bash start.sh`; on **Windows** run
   `powershell -ExecutionPolicy Bypass -File .\\start.ps1`.
4. Open **http://127.0.0.1:8000/** — web UI and API share the same origin.
   Keep the terminal running. Ctrl+C stops the server.

The bundled wheel and UI are packaged by GitHub Actions and an extracted
bundle is validated against **real GPT-2 inference using a browser** before
it can be uploaded as a verified release candidate.
See [M8 release guide](docs/M8_RELEASE.md) and
[M8 packaging architecture](docs/M8_PACKAGING.md) and [measured M8 validation](docs/M8_VALIDATION.md).

The ZIP does **not** include model weights, downloaded Python packages,
or the Python interpreter itself. Internet access is needed on first install.
**Linux x86-64 and Apple Silicon macOS packaged-run validation succeeded.**
The [Apple MPS smoke test](https://github.com/parksy1625/cortex-debugger/actions/runs/40011896404)
downloaded the published ZIP, executed `bash start.sh`, and completed a
real GPT-2 MPS experiment. Windows PowerShell installation and real GPT-2 CPU inference are also validated by [Windows M9 CI](https://github.com/parksy1625/cortex-debugger/actions/runs/40016740044).

### Developer mode (source checkout)

```bash
python -m pip install -e '.[ml,api,dev]' -c requirements-linux-py311.lock
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm ci
npm run dev
# localhost:5173 (Vite -> API :8000)
```

Linux-only version constraints must **not** be used on Apple MPS or Windows.
PyTorch 2.7.1 CPU with the Linux Python 3.11 lockfile has been validated.
The pinned model revision is
`607a30d783dfa663caf39e06633721c8d4cfcd7e`.

### Scientific and privacy limitations

- The engine measures specified activation interventions and logit margins;
  a meaningful circuit is **not** proven merely by an intervention changing
  the output. Same-run self-patching controls and strict replay comparisons
  are included.
- Exported full evidence can include token IDs; manifests contain **raw
  prompts**. Redacted summaries exclude both but still reveal measurements.
- SQLite record deletion is not secure erasure of WAL, backups or snapshots.
- Server is unauthenticated. It is **localhost-only**; never expose it on a
  public/network interface or use multiple Uvicorn workers.
- CPU/MPS parity is supported by limited model-backed smoke evidence, not a
  cross-model benchmark; macOS and Windows bootstrap installation were tested on hosted runners; native GUI interaction and code signatures remain unverified.

Previous measured validation: [M7 report](docs/M7_VALIDATION.md) ·
[M6 subprocess isolation](docs/M6_VALIDATION.md).

MIT license.
