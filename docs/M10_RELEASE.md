# Cortex Debugger v0.10.0-rc1 local release candidate

Unzip this runtime bundle. It contains the compiled browser application, the
Cortex Python engine wheel, FastAPI runtime, local-only platform launch
scripts, the license and Linux Python dependency version constraints.
It does **not** include Python itself, model weights or Torch wheels.

## Start

- Linux/macOS: install Python 3.11+, then `bash start.sh`.
- Windows: install Python 3.11+, then
  `powershell -ExecutionPolicy Bypass -File .\\start.ps1`.
- Open `http://127.0.0.1:8000`. Use Ctrl+C in the terminal to stop.

Dependencies and pinned GPT-2 weights can download during first use. M10
adds a first-run runtime readiness panel that checks installed PyTorch,
TransformerLens, Python and free disk space without loading the model.

## Security scope

M10 rejects unexpected Host headers, malicious webpage Origin headers and
cross-site browser requests. It also bounds worker IPC responses to 1 MiB.
These are **defense-in-depth**, not local-user authentication. Other programs
on the same machine may still access the unauthenticated loopback API.
Do not expose the server on a LAN or public network, or use a shared
adversarial environment.

Full evidence and regression manifests may expose prompts or token IDs.
Logical SQLite row deletion is not secure erasure of WAL/backups.
The release is an unsigned bootstrap ZIP, not a fully independent
application executable or notarized package.
