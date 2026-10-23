# Cortex Debugger M8 — Local runtime bundle (release candidate)

This ZIP contains the **compiled React UI**, a Python engine wheel and the
local FastAPI backend source. It does not include model weights, an operating
system app installer, or an executable with bundled Python. On first launch,
dependencies and pinned GPT-2 weights may be downloaded from the internet.

## Start
Unzip into a directory you own (do not run from inside a ZIP). Install Python
3.11+; then run:

- **macOS or Linux**: in Terminal, `bash start.sh`
- **Windows**: PowerShell, `powershell -ExecutionPolicy Bypass -File .\start.ps1`

Once the server says ready, open **http://127.0.0.1:8000/**. Only a local
loopback interface is bound. Keep the terminal open; Ctrl+C stops the app.
The web screen and API are served on the same port, without Node or Vite.

On a GitHub-hosted Linux x86-64 runner, the bundle script installs the
previously validated Torch 2.7.1 CPU wheel and uses
`requirements-linux-py311.lock` as a version constraint. **macOS and Windows
installations have not yet been end-to-end validated from this ZIP.**
Their native Torch 2.7.1 environment should be verified before scientific
interpretation. Apple MPS requires compatible PyTorch/Mac hardware, and can be
selected in the browser UI.

## Local data and privacy

By default, SQLite reports are stored under `~/.cortex-debugger`; you can
set `CORTEX_DATA_DIR` to another local folder. This is a localhost-only
development tool. Do not bind the unauthenticated API to any public address.

Full evidence may include prompt token IDs. Regression manifests contain
literal raw prompts. Redacted reports omit the inputs but can reveal
aggregate measurements. Deleting a SQLite record is not secure erasure of
backups, journal files or filesystem snapshots.

## Packaging validation

GitHub's "Bundle smoke and release" workflow unpacks the very ZIP that it
uploads, creates a fresh environment, installs the included wheel, serves the
compiled UI and checks API health and model behavior. Refer to that workflow
for the specific release candidate's status; do not infer validation from the
presence of the ZIP alone.

This ZIP is not code-signed or notarized. SHA-256 checksums are provided by
the Actions workflow and tag-based release job if/when a release tag is
created. No permanent download link is promised for expiring CI artifacts.
