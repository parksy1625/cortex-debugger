"""One-time desktop-browser pairing with process-scoped bearer capabilities.

Credentials are never written to SQLite, URLs, logs or browser localStorage.
A bearer token is kept only in the current browser tab's sessionStorage.
This protects against unauthenticated local HTTP clients that do not have
the pairing code; it is *not* a same-OS-user privilege boundary.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import threading
import time


class PairingSession:
    def __init__(self, code: str, ttl_seconds: int = 600, max_attempts: int = 8):
        if not re.fullmatch(r"[0-9]{9}", code):
            raise ValueError("Pairing code must contain exactly nine decimal digits")
        self._code_hash = hashlib.sha256(code.encode("ascii")).digest()
        self._token_hash: bytes | None = None
        self._deadline = time.monotonic() + ttl_seconds
        self._max_attempts = max_attempts
        self._attempts = 0
        self._lock = threading.Lock()

    def authorized(self, header: str | None) -> bool:
        if not header or not header.startswith("Bearer "):
            return False
        token = header.removeprefix("Bearer ")
        if len(token) > 128:
            return False
        with self._lock:
            return self._token_hash is not None and hmac.compare_digest(
                self._token_hash, hashlib.sha256(token.encode("utf-8")).digest()
            )

    def pair(self, code: str) -> tuple[str | None, str]:
        with self._lock:
            if self._token_hash is not None:
                return None, "already_paired"
            if time.monotonic() > self._deadline:
                return None, "expired"
            if self._attempts >= self._max_attempts:
                return None, "locked"
            self._attempts += 1
            if not hmac.compare_digest(
                self._code_hash, hashlib.sha256(code.encode("utf-8")).digest()
            ):
                return None, "invalid"
            token = secrets.token_urlsafe(32)
            self._token_hash = hashlib.sha256(token.encode("ascii")).digest()
            # After successful pairing, no second token can be minted from
            # the code. Restart the server to create a new pairing session.
            return token, "paired"


def pairing_from_environment() -> PairingSession | None:
    # Drop the code from the process environment as early as possible so the
    # model worker does not inherit it. Launch scripts can show it once.
    code = os.environ.pop("CORTEX_PAIRING_CODE", None)
    if code is None:
        return None
    return PairingSession(code)
