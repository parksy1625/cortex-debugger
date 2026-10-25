"""M11 desktop pairing: limited one-time code, bearer gating, browser-origin defense."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.pairing import PairingSession, pairing_from_environment

CODE = "123456789"
PATH = "/api/v1/metrics/margin"
DATA = {"correct_logit": 3, "incorrect_logit": 2}


@pytest.fixture
def paired_client():
    original = app.state.pairing
    app.state.pairing = PairingSession(CODE, max_attempts=5)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.state.pairing = original


def test_fail_closed_until_browser_pairing(paired_client):
    client = paired_client
    assert client.get("/api/v1/auth/status").json() == {
        "enabled": True, "authenticated": False
    }
    assert client.get("/api/v1/models").status_code == 401
    assert client.get("/api/v1/experiments").status_code == 401
    assert client.post(PATH, json=DATA).status_code == 401
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/setup").status_code == 200


def test_one_time_pairing_token_then_replay_denied(paired_client):
    client = paired_client
    bad = client.post("/api/v1/auth/pair", json={"code": "999999999"})
    assert bad.status_code == 403
    assert CODE not in bad.text
    ok = client.post("/api/v1/auth/pair", json={"code": CODE})
    assert ok.status_code == 200
    token = ok.json()["token"]
    assert len(token) >= 40
    assert CODE not in json.dumps(ok.json())
    assert client.post("/api/v1/auth/pair", json={"code": CODE}).status_code == 403
    assert client.post(PATH, json=DATA).status_code == 401
    headers = {"Authorization": "Bearer " + token}
    assert client.post(PATH, json=DATA, headers=headers).json()["margin"] == 1
    assert client.get("/api/v1/models", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/status", headers=headers).json()["authenticated"]
    assert client.get("/api/v1/auth/status").json()["authenticated"] is False
    assert client.post(PATH, json=DATA, headers={
        "Authorization": "Bearer " + "a" * len(token)
    }).status_code == 401


def test_pairing_rate_limit_and_expired_codes(paired_client):
    client = paired_client
    for _ in range(5):
        assert client.post("/api/v1/auth/pair", json={"code": "000000000"}).status_code == 403
    assert client.post("/api/v1/auth/pair", json={"code": CODE}).status_code == 429
    session = PairingSession(CODE, ttl_seconds=-1)
    assert session.pair(CODE)[1] == "expired"


def test_host_origin_protection_applies_to_pairing(paired_client):
    client = paired_client
    assert client.post("/api/v1/auth/pair", json={"code": CODE}, headers={
        "Host": "untrusted.example"
    }).status_code == 400
    assert client.post("/api/v1/auth/pair", json={"code": CODE}, headers={
        "Origin": "https://malicious.example"
    }).status_code == 403
    assert client.post("/api/v1/auth/pair", json={"code": CODE}, headers={
        "Sec-Fetch-Site": "cross-site"
    }).status_code == 403
    assert client.post("/api/v1/auth/pair", json={"code": CODE}).status_code == 200


def test_pair_code_removed_from_worker_environment(monkeypatch):
    monkeypatch.setenv("CORTEX_PAIRING_CODE", CODE)
    assert pairing_from_environment() is not None
    assert "CORTEX_PAIRING_CODE" not in __import__("os").environ


def test_malformed_code_never_becomes_session():
    with pytest.raises(ValueError):
        PairingSession("password")
    with pytest.raises(ValueError):
        PairingSession("12345678")
    with pytest.raises(ValueError):
        PairingSession("1234567890")
