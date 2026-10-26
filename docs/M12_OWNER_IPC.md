# M12 phase 1 — owner-verified POSIX control IPC

**State: development on main, NOT in the published v0.11.0-rc1 ZIP.**

The M11 browser API still requires one-time pairing and a session bearer.
M12 phase 1 adds a separate, **operating-system peer-verified** control
channel for local status inspection and experiment cancellation.

## Architecture

On Linux and macOS, the bundled shell launcher enables
`CORTEX_OWNER_IPC=1`. FastAPI's application lifespan starts a Unix-domain
stream socket at `<CORTEX_DATA_DIR>/ipc/control.sock`; if the resulting path
would exceed the portable Unix-domain socket pathname limit, it uses a
deterministically named **private directory under /tmp** instead.
The socket's parent directory is mode `0700`, the socket is mode `0600`.

The server obtains the **kernel-reported peer UID** on every connection:
- Linux: `SO_PEERCRED` (pid, UID, GID)
- macOS: libc `getpeereid(fd, &euid, &egid)`

If the effective user ID differs from the running server's, the connection
is rejected. Platforms without these APIs fail closed rather than trust
client-supplied identifiers.

Only a deliberately limited JSON-line command protocol is accepted, with
a maximum 8,192-byte line. It supports `status` (model worker metadata,
without raw prompts) and `cancel` for a validated 32-digit experiment id.
The IPC socket is removed during graceful shutdown and stale, owner-owned
socket files can be reclaimed safely. An existing live listener, symlink,
non-socket file, wrong owner or permissive IPC directory is rejected.

The authenticated browser routes are **not yet transported through this
socket** and cannot be described as protected by OS peer credentials.
Windows continues to use M11 browser bearer authentication; named pipes
with verified peer SID and strict DACL are future work.

## Local owner CLI (Linux/macOS development environment)

Start the API in one terminal with `CORTEX_OWNER_IPC=1`. When the app
runs from the local shell bootstrap, this flag is set automatically.

```bash
python -m apps.api.owner_ipc status
python -m apps.api.owner_ipc cancel 0123456789abcdef0123456789abcdef
```

If using `CORTEX_DATA_DIR`, pass the same directory through `--data-dir`
or export the same environment in the control terminal. The socket path is
derived locally; no secret is printed or written into a public endpoint.

## Verification

- Actual Linux kernel peer-UID check and separate-client subprocess.
- The same test suite is run on Apple Silicon macOS with libc getpeereid.
- `0700` directory and `0600` socket permissions, wrong-UID rejection,
  oversized/malformed commands, active-socket refusal, symlink protection,
  and lifespan cleanup.

These tests do **not** establish a security boundary against a malicious
process running under the **same** account. That process naturally has
the same UID and may use the control socket. True privilege separation
would require OS isolation and more restrictive process accounts.

No code-signing certificates, remote interface or security keys are added.
M12 must have a separate versioned release after its own packaged model
and native platform tests; the pre-existing M11 release remains unchanged.
