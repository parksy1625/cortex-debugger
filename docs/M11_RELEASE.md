# Cortex Debugger v0.11.0-rc1 — paired localhost app

This is an unsigned **local bootstrap ZIP** containing a Python engine wheel,
compiled React application, FastAPI source runtime and launch scripts. It
does not include the Python interpreter, Torch wheels or GPT-2 weights.
Install Python 3.11+ and use internet for the first setup.

## Install and pair

Extract the ZIP, then run `bash start.sh` (Linux/macOS) or
`powershell -ExecutionPolicy Bypass -File .\\start.ps1` (Windows).
Open `http://127.0.0.1:8000/`. Enter the **nine-digit pairing code**
displayed by the Terminal or Windows GUI app. It expires after ten minutes,
supports eight attempts and is one-time use. Closing/restarting the server
invalidates the session; restart if you need to pair again.

If launched without a console, use the native GUI app's displayed code.
For automated test runners, `CORTEX_PAIRING_CODE` may supply a code in the
process environment. Do **not** put real production codes into shared
logfiles, release manifests, source control or shell command history.

Once paired, a fresh 256-bit bearer is kept in the current browser tab's
`sessionStorage`. It is not included in URLs, cookies, localStorage,
SQLite experiment data or model output. The local API rejects model/history
requests without the correct token.

## What authentication does NOT guarantee

A malicious local program with the same OS user can potentially inspect
processes and browser data or intercept the pairing code. This is not
user-peer-credential-verified Unix socket or Windows named pipe isolation.
Keep the service bound to `127.0.0.1`, never a LAN/public interface.
Browser Host/Origin restrictions and 1MiB subprocess response limits are
defense-in-depth and do not make arbitrary third-party models safe.

The application and launchers remain **unsigned**, and macOS Finder GUI
interactions/Windows desktop button clicks are not automatically tested.
Full experimental evidence and regression manifests may contain prompt
tokens and text; deletion is logical, not secure physical erasure.
