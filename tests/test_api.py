from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health():
    result = client.get("/api/v1/health")
    assert result.status_code == 200
    assert result.json()["stage"] == "M0"


def test_models_are_allowlisted():
    result = client.get("/api/v1/models")
    assert result.json()["models"][0]["id"] == "openai-community/gpt2"


def test_recovery():
    result = client.post("/api/v1/metrics/recovery", json={
        "clean_score": 2.0, "corrupted_score": 0.0, "patched_score": 1.0
    })
    assert result.status_code == 200
    assert result.json()["recovery"] == 0.5


def test_reject_invalid_score():
    result = client.post("/api/v1/metrics/recovery", json={
        "clean_score": "NaN", "corrupted_score": 0.0, "patched_score": 1.0
    })
    assert result.status_code == 422
