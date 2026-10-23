"""M2 API integration tests using a deterministic fake model runner."""
import json
import sqlite3
import threading
import time

import pytest
from fastapi.testclient import TestClient

from apps.api.experiments import ExperimentManager
from apps.api.main import app

DATA = {"clean":"The dog runs","corrupted":"The cat runs",
        "correct_token":" dog","incorrect_token":" cat",
        "layer":5,"token_index":1,"device":"cpu"}

@pytest.fixture
def client(tmp_path):
    def fake_runner(args):
        return {"status":"pass","activation_rms_delta":[[0.1,0.4],[0.2,0.7]],
                "scores":{"clean":2.0,"corrupted":1.0,"patched":1.7,"recovery":0.7},
                "control":{"max_abs_logit_delta":0.0,"tolerance":1e-4}}
    manager=ExperimentManager(tmp_path/"experiments.sqlite3",runner=fake_runner)
    app.state.experiment_manager=manager
    with TestClient(app) as api:
        yield api,manager
    manager.shutdown()
    del app.state.experiment_manager

def finish(api,experiment_id):
    for _ in range(150):
        item=api.get(f"/api/v1/experiments/{experiment_id}").json()
        if item["status"] in ("completed","failed","cancelled"):
            return item
        time.sleep(.01)
    raise AssertionError("worker did not terminate")

def test_experiment_lifecycle_and_no_raw_prompt(client):
    api,manager=client
    r=api.post("/api/v1/experiments",json=DATA)
    assert r.status_code==202
    experiment_id=r.json()["id"]
    completed=finish(api,experiment_id)
    assert completed["status"]=="completed"
    assert completed["result"]["scores"]["recovery"]==0.7
    assert api.get("/api/v1/experiments?limit=1").json()["items"][0]["id"]==experiment_id
    with sqlite3.connect(manager.path) as conn:
        raw=json.dumps(conn.execute("SELECT * FROM experiments").fetchall())
    assert DATA["clean"] not in raw
    assert DATA["corrupted"] not in raw

@pytest.mark.parametrize("change",[
    {"clean":" "},{"layer":12},{"token_index":128},{"device":"cuda"},
    {"revision":"main"},{"corrupted":"x"*601}
])
def test_reject_invalid_request(client,change):
    api,_=client
    assert api.post("/api/v1/experiments",json={**DATA,**change}).status_code==422

def test_nonexistent_or_malformed_id(client):
    api,_=client
    assert api.get("/api/v1/experiments/nope").status_code==404
    assert api.get("/api/v1/experiments/"+"f"*32).status_code==404

def test_error_message_does_not_echo_private_prompt(client):
    api,manager=client
    def raises(args):
        raise RuntimeError("sensitive: "+args["clean"])
    manager.runner=raises
    experiment_id=api.post("/api/v1/experiments",json=DATA).json()["id"]
    record=finish(api,experiment_id)
    assert record["status"]=="failed"
    assert DATA["clean"] not in json.dumps(record)

def test_queue_limit_and_queued_cancel(tmp_path):
    started=threading.Event()
    release=threading.Event()
    def slow(args):
        started.set()
        release.wait(3)
        return {"status":"pass"}
    manager=ExperimentManager(tmp_path/"queue.sqlite3",runner=slow,max_outstanding=2)
    app.state.experiment_manager=manager
    try:
        with TestClient(app) as api:
            first=api.post("/api/v1/experiments",json=DATA).json()["id"]
            assert started.wait(2)
            second=api.post("/api/v1/experiments",json=DATA).json()["id"]
            assert api.post("/api/v1/experiments",json=DATA).status_code==429
            assert api.post(f"/api/v1/experiments/{first}/cancel").status_code==409
            assert api.post(f"/api/v1/experiments/{second}/cancel").json()["status"]=="cancelled"
            assert api.get(f"/api/v1/experiments/{second}").json()["status"]=="cancelled"
    finally:
        release.set()
        manager.shutdown()
        del app.state.experiment_manager


def test_history_limit_is_validated(client):
    api,_=client
    assert api.get('/api/v1/experiments?limit=0').status_code == 422
    assert api.get('/api/v1/experiments?limit=51').status_code == 422


def test_reopen_marks_interrupted_jobs_failed(tmp_path):
    path = tmp_path / "restart.sqlite3"
    manager = ExperimentManager(path, runner=lambda _args: {"status": "pass"})
    manager.shutdown()
    with sqlite3.connect(path) as conn:
        for identifier, state in [("a" * 32, "queued"), ("b" * 32, "running")]:
            conn.execute(
                "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, NULL, NULL)",
                (identifier, state, "2026-01-01", "2026-01-01", "{}"),
            )
    recovered = ExperimentManager(path, runner=lambda _args: {"status": "pass"})
    try:
        for identifier in ("a" * 32, "b" * 32):
            record = recovered.get(identifier)
            assert record["status"] == "failed"
            assert record["error"] == "Interrupted by worker restart"
    finally:
        recovered.shutdown()
