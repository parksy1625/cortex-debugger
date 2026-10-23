"""M7 privacy-safe export and local experiment deletion."""
from __future__ import annotations

import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from apps.api.experiments import ExperimentManager
from apps.api.main import app
from apps.api.privacy import shareable_report

PRIVATE = "My confidential prompt 839103"

DATA = {
    "clean": PRIVATE, "corrupted": "another hidden input",
    "correct_token": " dog", "incorrect_token": " cat",
    "layer": 5, "token_index": 2, "device": "cpu",
}


def evidence():
    return {
        "schema_version": 1, "status": "pass",
        "model": {"id": "openai-community/gpt2", "revision": "a" * 40, "device": "cpu"},
        "input": {
            "clean_sha256": "secret_fingerprint",
            "corrupted_sha256": "another_fingerprint",
            "clean_token_ids": [11, 22, 33],
            "corrupted_token_ids": [44, 55],
            "candidate_token_ids": {"correct": 22, "incorrect": 55},
        },
        "patch": {"layer": 5, "token_index": 2, "site": "blocks.5.hook_out"},
        "scores": {"clean": 2.0, "corrupted": -1.0, "patched": 1.0, "recovery": 0.6667},
        "control": {"max_abs_logit_delta": 0.0, "tolerance": 1e-4},
        "execution": {"secret_path": "/private/user/model"},
        "runtime_seconds": 1.2,
    }


def test_redacted_allowlist_omits_private_identifiers():
    record = {"id": "9" * 32, "status": "completed", "result": evidence()}
    exported = shareable_report(record)
    raw = json.dumps(exported)
    assert exported["kind"] == "cortex-redacted-summary"
    assert exported["redacted"] is True
    assert exported["scores"]["recovery"] == pytest.approx(.6667)
    assert "secret_fingerprint" not in raw
    assert "candidate_token_ids" not in raw
    assert '"id": "999' not in raw
    assert "/private/user" not in raw
    assert "clean_token_ids" not in raw
    assert PRIVATE not in raw
    assert '"experiment":' not in raw


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(status="running"),
    lambda x: x["result"].update(status="fail"),
    lambda x: x["result"]["scores"].update(patched=float("nan")),
    lambda x: x["result"].pop("control"),
])
def test_redact_refuses_unsafe_or_incomplete_results(mutation):
    record = {"status": "completed", "result": evidence()}
    mutation(record)
    with pytest.raises(ValueError):
        shareable_report(record)


@pytest.fixture
def api(tmp_path):
    manager = ExperimentManager(tmp_path / "privacy.sqlite3", runner=lambda _args: evidence())
    app.state.experiment_manager = manager
    try:
        with TestClient(app) as client:
            yield client, manager
    finally:
        manager.shutdown()
        del app.state.experiment_manager


def finished(client, identifier):
    for _ in range(100):
        record = client.get("/api/v1/experiments/" + identifier).json()
        if record["status"] in ("completed", "failed", "cancelled"):
            return record
        time.sleep(.01)
    raise AssertionError("worker did not finish")


def test_api_export_and_delete_record(api):
    client, manager = api
    job = client.post("/api/v1/experiments", json=DATA).json()["id"]
    assert finished(client, job)["status"] == "completed"
    exported = client.get(f"/api/v1/experiments/{job}/shareable")
    assert exported.status_code == 200
    content = exported.text
    assert "clean_token_ids" not in content
    assert "secret_fingerprint" not in content
    assert job not in content
    assert PRIVATE not in content
    deleted = client.delete(f"/api/v1/experiments/{job}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/experiments/{job}").status_code == 404
    assert client.get(f"/api/v1/experiments/{job}/shareable").status_code == 404
    assert client.delete(f"/api/v1/experiments/{job}").status_code == 404
    assert all(item["id"] != job for item in client.get("/api/v1/experiments").json()["items"])
    with sqlite3.connect(manager.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM experiments WHERE id=?", (job,)).fetchone()[0] == 0


def test_cannot_delete_queued_or_running_job(tmp_path):
    import threading

    start = threading.Event()
    release = threading.Event()

    def blocked(_args):
        start.set()
        release.wait(2)
        return evidence()

    manager = ExperimentManager(tmp_path / "pending.sqlite3", runner=blocked)
    app.state.experiment_manager = manager
    try:
        with TestClient(app) as client:
            first = client.post("/api/v1/experiments", json=DATA).json()["id"]
            assert start.wait(1)
            second = client.post("/api/v1/experiments", json=DATA).json()["id"]
            assert client.delete(f"/api/v1/experiments/{first}").status_code == 409
            assert client.delete(f"/api/v1/experiments/{second}").status_code == 409
            assert client.post(f"/api/v1/experiments/{second}/cancel").status_code == 200
            assert client.delete(f"/api/v1/experiments/{second}").status_code == 204
    finally:
        release.set()
        manager.shutdown()
        del app.state.experiment_manager
