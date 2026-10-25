# M11 phase 1 — one-time browser pairing

## Behavior

- Shell/PowerShell startup creates a cryptographically random nine-digit
  pairing code on every application launch; Windows desktop launcher
  generates and displays one in its GUI. The server consumes and removes
  the code from its environment on import, preventing the model worker
  subprocess from inheriting it after server initialization.
- The code is valid for ten minutes from API startup, limited to eight
  guesses, and can be exchanged **once** for a random 256-bit bearer.
- Only one browser session is authorized at a time. Restart server to
  pair again; previous bearers are invalid on restart.
- The token is returned through a same-origin POST response and retained
  in tab-level browser `sessionStorage`, not cookies, URL parameters,
  SQLite records or localStorage. `Authorization: Bearer` protects all
  other `/api/v1/*` endpoints except public health, setup and auth status.
- Existing M10 Host, Origin, Fetch-Site and IPC protections remain.

## Threat boundaries

This is genuine application-level HTTP bearer authorization, but **not
same-user OS-level authentication**: a malicious process under the same
Windows/macOS user can inspect local process configuration, browser memory,
or intercept the user's code. A local attacker can also deliberately exhaust
the allowed code attempts, causing denial of service until restart.
Do not expose the service to the network. Use a future dedicated local
IPC channel with verified OS peer credentials for stronger guarantees.

## Compatibility

Production M11 bootstrap launchers enable pairing by supplying
`CORTEX_PAIRING_CODE`. Raw `uvicorn` in a source checkout does not
auto-generate an accessible code; absent the environment variable, it
retains unauthenticated *development mode* for compatibility. To test the
authenticated source server manually, set the code **privately** in the
process environment and launch `uvicorn` on `127.0.0.1`; do not put
production pairing codes into shell history or shared logs.

## Release

The `v0.11.0-rc1` release is now published with independently verified
Linux, Apple Silicon MPS, and Windows CPU bootstrap packages. Prior v0.10
release assets were not overwritten. See [measured evidence](M11_VALIDATION.md).
