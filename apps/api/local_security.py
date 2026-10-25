"""Browser-origin and DNS-rebinding safeguards for localhost research API.

This is *not* authentication: a malicious local process can speak HTTP to
loopback directly and spoof Origin/Host. It prevents access from untrusted
webpage origins in conventional browsers and rejects hostile Host headers.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _authority(value: str) -> tuple[str, int | None, str] | None:
    """Strict origin/host syntax, no credentials, fragments or opaque origins."""
    if not value or value != value.strip():
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        if parsed.path or parsed.query or parsed.fragment:
            return None
        host = parsed.hostname
        if host is None:
            return None
        return host.lower(), parsed.port, parsed.scheme
    except ValueError:
        return None


def _host_valid(request: Request) -> bool:
    value = request.headers.get("host", "")
    # URL parsing eliminates trailing-dot, encoded, domain suffix, and
    # credentials tricks without ever resolving untrusted DNS.
    parsed = _authority("http://" + value)
    if parsed is None:
        return False
    host, _, _ = parsed
    if host in _ALLOWED_HOSTS:
        return True
    # Starlette's TestClient uses testserver/testclient, not a real listener.
    return host == "testserver" and request.client is not None and (
        request.client.host == "testclient"
    )


def _origin_allowed(request: Request, origin: str) -> bool:
    src = _authority(origin)
    host = _authority("http://" + request.headers.get("host", ""))
    if src is None or host is None:
        return False
    dev_origin = os.getenv("CORTEX_DEV_ORIGIN", "")
    if dev_origin and src == _authority(dev_origin):
        # Only opt-in a loopback development host; never arbitrary URLs.
        return src[0] in _ALLOWED_HOSTS
    return src[0] == host[0] and src[1] == host[1] and src[2] in (
        "http", "https"
    )


async def protect_local_requests(request: Request, call_next):
    if not _host_valid(request):
        return JSONResponse({"detail": "Local host required"}, status_code=400)
    fetch_site = request.headers.get("sec-fetch-site", "").lower()
    if fetch_site == "cross-site":
        return JSONResponse({"detail": "Cross-site browser access denied"}, status_code=403)
    origin = request.headers.get("origin")
    if fetch_site == "same-site" and not (
        origin is not None and os.getenv("CORTEX_DEV_ORIGIN") and _origin_allowed(request, origin)
    ):
        return JSONResponse({"detail": "Cross-site browser access denied"}, status_code=403)
    if origin is not None and not _origin_allowed(request, origin):
        return JSONResponse({"detail": "Request origin denied"}, status_code=403)
    # Reject simple cross-origin form submissions lacking Origin as a browser
    # defense-in-depth; requests from API clients without browser metadata
    # remain supported for the existing CLI and smoke tests.
    if request.method in _UNSAFE and fetch_site == "none":
        return JSONResponse({"detail": "Browser mutation origin required"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response
