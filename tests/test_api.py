from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["stage"] == "M6"

def test_models_are_allowlisted():
    assert client.get("/api/v1/models").json()["models"][0]["id"] == "openai-community/gpt2"

def test_recovery():
    response = client.post("/api/v1/metrics/recovery", json={
        "clean_score":2.0,"corrupted_score":0.0,"patched_score":1.0
    })
    assert response.status_code==200
    assert response.json()["recovery"]==0.5

def test_reject_invalid_score():
    assert client.post("/api/v1/metrics/recovery",json={
        "clean_score":"NaN","corrupted_score":0.0,"patched_score":1.0
    }).status_code==422
