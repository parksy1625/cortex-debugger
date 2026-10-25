# M10 browser-origin protection and first-run readiness

## Browser security protection

The M9 public release is a localhost-only HTTP API without authentication.
M10 adds *browser-focused defenses* but does **not** make the API safe from
malicious software that can issue local HTTP requests.

- Reject non-loopback Host headers, including DNS-rebinding hostnames
  `localhost.attacker.test` and `127.0.0.1.evil.test`.
- Reject `Origin: null`, hostile origins and `Sec-Fetch-Site: cross-site`.
- For unsafe operations (POST, PUT, PATCH, DELETE), enforce same-origin
  browser requests; requests from nonbrowser test/CLI clients that send
  no browser metadata remain compatible.
- Strictly allow one optional local Vite development origin when
  `CORTEX_DEV_ORIGIN=http://127.0.0.1:5173` is set.
- Add `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`
  and `Cache-Control: no-store` response headers.
- Do not enable CORS wildcard or permit remote exposure.

**Threat boundary:** Other processes on the same computer can spoof
Host/Origin and access local HTTP services. These safeguards reduce
malicious website and DNS-rebinding exposure, but are not a substitute
for authenticated local IPC, user permissions, or a session capability.

## Setup readiness

`GET /api/v1/setup` reports operating system, CPU architecture, Python
version and compatibility, whether PyTorch and TransformerLens modules are
installed, and available storage in approximate gigabytes. It does not
import Torch, load GPT-2 or return usernames, files or private paths.
The React Studio shows this as a small responsive readiness panel; the
user can refresh the diagnosis without creating an experiment.

The actual first GPT-2 inference may still require a network download and
substantial local memory. `torch_installed=true` indicates an importable
module name, not guaranteed native backend functionality.

## Developer Vite exception

```bash
CORTEX_DEV_ORIGIN=http://127.0.0.1:5173 python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Production ZIP/.app/.exe uses compiled UI on port 8000: the exception is
unnecessary. Never set `CORTEX_DEV_ORIGIN` to an internet domain.

## Release status

M10 changes on main are **development work**, not yet packaged into the
existing published v0.9.0-rc1 assets. A new version/tag and platform
validation are required before describing these improvements as shipped.

## Worker IPC protection (M10)

The isolated model process now accepts a maximum 1 MiB JSON-line response.
The parent uses bounded `readline()` calls and terminates a worker that
sends an oversize result before decoding JSON. This caps *a single worker
message* in the parent. Model memory and result processing remain subject
to separate resource limits; this is not an arbitrary-code sandbox.
