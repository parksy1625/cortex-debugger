"""M10: localhost browser security and safe setup diagnostics.

These checks defend against DNS rebinding and browser cross-origin requests;
they do NOT authenticate other local OS users or processes.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


def test_host_header_rebinding_is_denied():
    client = TestClient(app)
    assert client.get("/api/v1/health", headers={"host": "evil.example"}).status_code == 400
    assert client.get("/api/v1/health", headers={"host": "localhost.attacker.test"}).status_code == 400
    assert client.get("/api/v1/health", headers={"host": "127.0.0.1.evil.test"}).status_code == 400
    assert client.get("/api/v1/health", headers={"host": "localhost."}).status_code == 400
    assert client.get("/api/v1/health", headers={"host": "127.0.0.1:8000"}).status_code == 200
    assert client.get("/api/v1/health", headers={"host": "[::1]:8000"}).status_code == 200


def test_cross_site_requests_denied_without_model_boot():
    client = TestClient(app)
    path = "/api/v1/metrics/margin"
    request = {"correct_logit": 2.0, "incorrect_logit": 1.0}
    assert client.post(path, json=request, headers={
        "host": "127.0.0.1:8000", "origin": "https://attacker.example",
    }).status_code == 403
    assert client.post(path, json=request, headers={
        "host": "127.0.0.1:8000", "origin": "null",
    }).status_code == 403
    assert client.post(path, json=request, headers={
        "host": "127.0.0.1:8000", "sec-fetch-site": "cross-site",
    }).status_code == 403
    assert client.get("/api/v1/health", headers={
        "host": "127.0.0.1:8000", "sec-fetch-site": "cross-site",
    }).status_code == 403
    assert client.post(path, json=request, headers={
        "host": "127.0.0.1:8000", "sec-fetch-site": "none",
    }).status_code == 403


def test_valid_local_browser_requests_preserved():
    client = TestClient(app)
    path = "/api/v1/metrics/margin"
    headers = {
        "host": "127.0.0.1:8000",
        "origin": "http://127.0.0.1:8000",
        "sec-fetch-site": "same-origin",
    }
    response = client.post(path, json={
        "correct_logit": 2, "incorrect_logit": 1,
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["margin"] == 1.0
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_opted_in_vite_development_origin(monkeypatch):
    monkeypatch.setenv("CORTEX_DEV_ORIGIN", "http://127.0.0.1:5173")
    client = TestClient(app)
    headers = {
        "host": "127.0.0.1:8000",
        "origin": "http://127.0.0.1:5173",
        "sec-fetch-site": "same-site",
    }
    assert client.post("/api/v1/metrics/margin", headers=headers, json={
        "correct_logit": 3, "incorrect_logit": 2,
    }).status_code == 200
    # An opt-in of one development origin is NOT a wildcard.
    assert client.post("/api/v1/metrics/margin", headers={
        **headers, "origin": "http://127.0.0.1:5174",
    }, json={"correct_logit": 3, "incorrect_logit": 2}).status_code == 403
    monkeypatch.setenv("CORTEX_DEV_ORIGIN", "https://evil.example")
    assert client.post("/api/v1/metrics/margin", headers={
        **headers, "origin": "https://evil.example",
    }, json={"correct_logit": 3, "incorrect_logit": 2}).status_code == 403


def test_setup_diagnostics_are_non_identifying_and_do_not_load_model():
    client = TestClient(app)
    result = client.get("/api/v1/setup")
    assert result.status_code == 200
    setup = result.json()
    assert setup["python_supported"] is True
    assert setup["os"] in ("Linux", "Darwin", "Windows")
    assert setup["free_disk_gb"] >= 0
    assert isinstance(setup["torch_installed"], bool)
    assert isinstance(setup["transformerlens_installed"], bool)
    assert "home" not in setup
    assert "/Users/" not in str(setup)
    assert "download" in str(setup)
