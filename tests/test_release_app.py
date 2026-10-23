"""Packaging smoke tests independent of heavyweight GPT-2 downloads."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.main import mount_built_studio


def test_static_app_mount_ignores_missing_build(tmp_path):
    app = FastAPI()
    assert mount_built_studio(app, tmp_path) is False
    assert TestClient(app).get("/").status_code == 404


def test_compiled_frontend_served_on_same_origin_as_api(tmp_path):
    index = tmp_path / "index.html"
    index.write_text("<html><title>Cortex Debugger UI</title></html>", encoding="utf-8")
    asset = tmp_path / "assets" / "main.js"
    asset.parent.mkdir()
    asset.write_text("window.cortexReady=true;", encoding="utf-8")
    app = FastAPI()

    @app.get("/api/v1/health")
    def api_health():
        return {"status": "ok", "local_only": True}

    assert mount_built_studio(app, tmp_path) is True
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "Cortex Debugger UI" in client.get("/").text
    assert client.get("/assets/main.js").status_code == 200
    assert "cortexReady" in client.get("/assets/main.js").text
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/nonexistent").status_code == 404


def test_static_mount_does_not_serve_unrelated_files(tmp_path):
    (tmp_path / "index.html").write_text("hi", encoding="utf-8")
    app = FastAPI()
    assert mount_built_studio(app, tmp_path)
    result = TestClient(app).get("/../../../../etc/passwd")
    assert "root:x:" not in result.text
