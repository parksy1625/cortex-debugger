"""Real GPT-2 integration through HTTP API. Opt-in: downloads pinned weights."""

from __future__ import annotations

import os
import time

import pytest
from cortex_engine.model_cache import MODEL_CACHE
from cortex_engine.pairing import DEFAULT_MODEL_REVISION
from fastapi.testclient import TestClient

from apps.api.experiments import ExperimentManager
from apps.api.main import app

pytestmark = pytest.mark.real_model

REQUEST = {
    "clean": "The dog runs", "corrupted": "The cat runs",
    "correct_token": " dog", "incorrect_token": " cat",
    "layer": 5, "token_index": 2, "device": "cpu",
    "revision": DEFAULT_MODEL_REVISION,
}


@pytest.mark.skipif(os.getenv("CORTEX_RUN_REAL_MODEL") != "1", reason="Requires real GPT-2 weights")
def test_real_http_api_uses_cached_weights(tmp_path):
    MODEL_CACHE.clear()
    manager = ExperimentManager(tmp_path / "live.sqlite3")
    app.state.experiment_manager = manager
    try:
        with TestClient(app) as client:
            outcomes = []
            for _ in range(2):
                submitted = client.post("/api/v1/experiments", json=REQUEST)
                assert submitted.status_code == 202
                job_id = submitted.json()["id"]
                deadline = time.monotonic() + 180
                while time.monotonic() < deadline:
                    response = client.get(f"/api/v1/experiments/{job_id}")
                    assert response.status_code == 200
                    record = response.json()
                    if record["status"] in ("completed", "failed", "cancelled"):
                        break
                    time.sleep(.2)
                else:
                    raise AssertionError("Real model worker exceeded integration deadline")
                assert record["status"] == "completed", record.get("error")
                evidence = record["result"]
                assert evidence["model"]["revision"] == DEFAULT_MODEL_REVISION
                assert evidence["control"]["max_abs_logit_delta"] <= 1e-4
                assert .75 < evidence["scores"]["recovery"] < 1.35
                assert REQUEST["clean"] not in str(record)
                outcomes.append(evidence)
            assert outcomes[0]["execution"]["model_cache_hit"] is False
            assert outcomes[1]["execution"]["model_cache_hit"] is True
            assert client.get("/api/v1/models").json()["models"][0]["loaded"] is True
            assert client.get("/api/v1/models").json()["models"][0]["cache_hits"] >= 1
    finally:
        manager.shutdown()
        del app.state.experiment_manager
        MODEL_CACHE.clear()
