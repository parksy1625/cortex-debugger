"""M8 macOS release-candidate smoke: real MPS model through packaged API."""

from __future__ import annotations

import json
import time
from urllib.request import Request, urlopen

HOST = "http://127.0.0.1:8000"
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"


def get(route: str) -> dict:
    with urlopen(HOST + route, timeout=15) as response:
        return json.load(response)


def main() -> None:
    status = get("/api/v1/health")
    assert status["status"] == "ok"
    assert status["stage"] == "M10"

    experiment = {
        "clean": "The dog runs",
        "corrupted": "The cat runs",
        "correct_token": " dog",
        "incorrect_token": " cat",
        "device": "mps",
        "revision": REVISION,
        "layer": 5,
        "token_index": 2,
    }
    request = Request(
        HOST + "/api/v1/experiments",
        data=json.dumps(experiment).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        submission = json.load(response)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        record = get("/api/v1/experiments/" + submission["id"])
        if record["status"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(1)
    else:
        raise AssertionError("MPS experiment timed out")
    if record["status"] != "completed":
        raise AssertionError(f"MPS execution failed: {record.get('error')}")
    evidence = record["result"]
    assert evidence["model"]["device"] == "mps"
    assert evidence["model"]["revision"] == REVISION
    assert evidence["control"]["max_abs_logit_delta"] < 0.0001
    recovery = evidence["scores"]["recovery"]
    assert isinstance(recovery, (float, int)) and 0.75 < recovery < 1.35
    assert get("/api/v1/models")["models"][0]["loaded"] is True
    print(json.dumps({
        "status": "pass",
        "backend": "real Apple Silicon MPS",
        "model_revision": REVISION,
        "recovery": recovery,
        "patch": evidence["patch"],
        "api_stage": status["stage"],
    }, indent=2))


if __name__ == "__main__":
    main()
