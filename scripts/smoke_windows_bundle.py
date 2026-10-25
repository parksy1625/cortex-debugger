"""Actual public M8 release ZIP, Windows native CPU/HTTP smoke test.

Does not log prompt contents. The parent Windows Actions workflow starts the
installed package from its PowerShell bootstrap script.
"""
from __future__ import annotations

import json
import os
import time
from urllib.request import Request, urlopen

HOST = "http://127.0.0.1:8000"
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
HEADERS: dict[str, str] = {}


def authorize() -> None:
    code = os.getenv("CORTEX_TEST_PAIRING_CODE")
    if not code:
        return
    request = Request(
        HOST + "/api/v1/auth/pair", method="POST",
        data=json.dumps({"code": code}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        token = json.load(response)["token"]
    HEADERS["Authorization"] = "Bearer " + token



def read(path: str) -> dict:
    with urlopen(Request(HOST + path, headers=HEADERS), timeout=20) as response:
        return json.load(response)


def main() -> None:
    assert read("/api/v1/health")["stage"] == "M11"
    authorize()
    with urlopen(HOST + "/", timeout=20) as response:
        assert b'<div id="root"' in response.read()
    payload = {
        "clean": "The dog runs",
        "corrupted": "The cat runs",
        "correct_token": " dog",
        "incorrect_token": " cat",
        "device": "cpu",
        "revision": REVISION,
        "layer": 5,
        "token_index": 2,
    }
    req = Request(
        HOST + "/api/v1/experiments",
        data=json.dumps(payload).encode("utf-8"),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as response:
        submitted = json.load(response)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        job = read("/api/v1/experiments/" + submitted["id"])
        if job["status"] in ("completed", "failed", "cancelled"):
            break
        time.sleep(1)
    else:
        raise AssertionError("Timed out waiting for real Windows GPT-2 experiment")
    assert job["status"] == "completed", job.get("error")
    result = job["result"]
    assert result["model"]["device"] == "cpu"
    assert result["model"]["revision"] == REVISION
    assert result["control"]["max_abs_logit_delta"] <= .0001
    recovery = result["scores"]["recovery"]
    assert .75 < recovery < 1.35
    assert read("/api/v1/models")["models"][0]["loaded"] is True
    print(json.dumps({
        "status": "pass", "platform": "Windows x64 native CPU",
        "revision": REVISION, "recovery": recovery, "api_stage": "M11",
    }, indent=2))


if __name__ == "__main__":
    main()
