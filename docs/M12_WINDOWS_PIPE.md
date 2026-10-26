# M12 Phase 2 — Windows owner SID named-pipe control

**Development on `main` only. This code is not included in the published
v0.11.0-rc1 ZIP, and is not yet a new M12 release.**

## Security boundary and implementation

On Windows, the app startup now enables `CORTEX_OWNER_IPC=1`.
The FastAPI lifespan instantiates a named-pipe controller for the signed-in
user. It derives a stable pipe name from a digest of the current user's SID
and the requested local data directory.

The pipe has:
- An explicit **DACL with a single access-allowed ACE for the running user's
  SID**; it does not rely on the Windows default named-pipe DACL, which may
  be permissive for anonymous/local readers.
- A `FILE_FLAG_FIRST_PIPE_INSTANCE` server handle that prevents replacement
  while running, and `PIPE_REJECT_REMOTE_CLIENTS` to prohibit remote SMB
  connections.
- Explicit client impersonation **after reading the request**, then
  `OpenThreadToken` and `TokenUser` identity comparison with the
  server user's SID. Failed impersonation or mismatched SID fails closed.
  `RevertToSelf` is executed in a `finally` block.
- A single-message **8192 byte maximum JSON-line protocol**. Only
  `status` (no prompts) and `cancel` (strict 32-digit lowercase hex
  experiment id) are permitted; arbitrary code/commands are not accepted.
- A bounded connection retry for the Windows single-pipe busy condition
  and explicit handle closure on shutdown.

**These controls authenticate the OS user account, not the specific
application executable or process.** A malicious process running under the
same Windows user SID can still connect. Administrator/SYSTEM compromise is
out of scope. The existing M11 browser HTTP routes still use one-time
pairing and bearer authorization; they have not moved to the named pipe.

## Windows development use

On a Windows source checkout installed with `pip install -e ".[api]"`:

```powershell
$env:CORTEX_OWNER_IPC = "1"
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

In a second PowerShell terminal under the **same Windows account**:

```powershell
python -m apps.api.owner_pipe_windows status
python -m apps.api.owner_pipe_windows cancel 0123456789abcdef0123456789abcdef
```

If `CORTEX_DATA_DIR` is customized, set it identically in the second
terminal or pass `--data-dir`. No raw prompt text is sent over this control
channel.

## Verification

- [Windows named-pipe CI #40296700666](https://github.com/parksy1625/cortex-debugger/actions/runs/40296700666)
  — **PASS: 7 tests** on `windows-2022`.
- The test suite checks real Windows pipe SID acquisition and client
  impersonation, explicit DACL ACE contents, mocked cross-SID refusal,
  invalid and oversized command handling, second-server takeover refusal,
  separate client process, and FastAPI lifespan start/stop.
- Linux/macOS POSIX IPC tests and live GPT-2 browser workflows run
  independently to detect regressions.

**Not yet tested:** another *real logged-in Windows user* attempting access
(runner has one test login), the GUI's click-driven pipe usage, Windows
packaged ZIP after M12 changes, signed MSI installers, or moving the entire
browser API to the OS-authenticated control channel.
