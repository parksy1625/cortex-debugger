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

## Security and validation limits

M11 one-time browser pairing is retained. A separate M12 owner-control IPC
channel uses kernel peer UID on Linux/macOS or token SID plus DACL on Windows;
the browser still communicates over paired loopback HTTP, **not** through
the OS-authenticated IPC channel. Same-user processes are not isolated.

Before any M12 release, require Windows native pipe tests, POSIX owner-control
tests on Ubuntu and Apple Silicon, real GPT-2 browser/API inference, packaged
runtime smoke checks, plus manual GUI and signing decisions. A successful ZIP
build alone does not qualify an installer or prove it is fully offline.
