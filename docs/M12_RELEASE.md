# Cortex Debugger v0.12.0-rc1 — source-built validation candidate

**Development candidate only. No v0.12.0-rc1 installer or release is published.**
The M12 candidate ZIP is built and tested from the source branch without
creating a GitHub Release or modifying historical v0.11.0-rc1 assets.

The bundle contains a Python engine wheel, compiled local Studio,
FastAPI runtime source, and macOS/Linux/Windows bootstrap scripts. It does
not contain Python, PyTorch wheels, GPT-2 weights, model cache, or user data.
Python 3.11+ and network access are required on first installation.

## Local developer validation

Build the `0.12.0rc1` Python wheel and the React production frontend, then:

```bash
python -m scripts.build_release --version v0.12.0-rc1
cd artifacts && sha256sum -c Cortex-Debugger-v0.12.0-rc1.zip.sha256
```

The release builder verifies that the requested ZIP version matches the wheel
version and rejects an existing destination rather than overwriting it.
The launchers track the exact bundled wheel SHA-256 and reinstall dependencies
when it changes; they only write the marker after a successful installation.
Both launchers now run the same dependency-free package preflight before
installing anything. `./start.sh --check` and `start.ps1 -Check` validate the
Python version, single compatible wheel, API and compiled UI files without
downloading packages, changing the runtime, or starting a server. The three-OS
ZIP CI smoke checks that native preflight too.

The unpublished M12 Actions workflow also downloads the *same ZIP artifact*
on Ubuntu, macOS and Windows, checks its SHA-256 again, extracts it into a
temporary directory, installs the bundled wheel with API dependencies in an
isolated Python environment, and boots only the extracted API. The smoke
checks the production UI, M12 health/version, unauthenticated API rejection,
single-use browser pairing and OS-specific owner IPC status. It intentionally
does not install PyTorch or download model weights; real GPT-2 tests remain a
separate release gate.

A separate Linux candidate job installs the bundled wheel with pinned CPU
PyTorch and model dependencies, starts the *extracted* server with pairing,
and runs the existing Chromium Playwright end-to-end experiment using actual
pinned GPT-2 weights. The browser test also verifies M12 API stage/version,
model revision, recovery and regression JSON export. This job is a required
piece of release evidence. The candidate workflow
[#40333501723](https://github.com/parksy1625/cortex-debugger/actions/runs/40333501723)
**passed** on 2026-10-26, including the Ubuntu/macOS/Windows ZIP matrix and
the real GPT-2 Chromium job. The tested ZIP was a source-runtime candidate,
not a native installer. Later Windows cross-account authorization changes
affect only the regression test/workflow, not the candidate runtime ZIP.

To repeat that quick check locally after downloading the ZIP and its matching
checksum sidecar into `artifacts/`:

```bash
python scripts/smoke_m12_candidate.py \
  --archive artifacts/Cortex-Debugger-v0.12.0-rc1.zip \
  --checksum artifacts/Cortex-Debugger-v0.12.0-rc1.zip.sha256
```

## Security and validation limits

M11 one-time browser pairing is retained. A separate M12 owner-control IPC
channel uses kernel peer UID on Linux/macOS or token SID plus DACL on Windows;
the browser still communicates over paired loopback HTTP, **not** through
the OS-authenticated IPC channel. Same-user processes are not isolated.

Before any M12 release, require Windows native pipe tests, POSIX owner-control
tests on Ubuntu and Apple Silicon, real GPT-2 browser/API inference, packaged
runtime smoke checks, plus manual GUI and signing decisions. A successful ZIP
build alone does not qualify an installer or prove it is fully offline.
