"""Local-only Cortex API. Bind to 127.0.0.1; do not expose unauthenticated endpoints."""
from __future__ import annotations

import importlib.util
from contextlib import asynccontextmanager
import os
import platform
import re
import shutil
import sys
import threading
from pathlib import Path
from typing import Literal

from cortex_engine import __version__
from cortex_engine.metrics import logit_margin, recovery_score
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from apps.api.experiments import ExperimentManager, NotCancellable, QueueFull
from apps.api.local_security import protect_local_requests
from apps.api.pairing import pairing_from_environment
from apps.api.privacy import shareable_report

@asynccontextmanager
async def app_lifespan(target_app: FastAPI):
    """Opt-in OS peer-verified admin IPC; web API retains browser pairing."""
    owner = None
    if os.environ.get("CORTEX_OWNER_IPC") == "1":
        if os.name != "posix":
            raise RuntimeError("Owner IPC on Windows needs named pipes; not yet implemented")
        from apps.api.owner_ipc import OwnerControl

        directory = Path(
            os.environ.get("CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger"))
        )
        def cancel_checked(job_id: str) -> bool:
            try:
                return get_manager_for_app(target_app).cancel(job_id)
            except NotCancellable:
                return False

        owner = OwnerControl(
            directory,
            get_status=lambda: get_manager_for_app(target_app).model_status(),
            cancel_job=cancel_checked,
        )
        owner.start()
        target_app.state.owner_control = owner
    try:
        yield
    finally:
        if owner is not None:
            owner.close()


app = FastAPI(
    title="Cortex Debugger API", version=__version__,
    docs_url="/api/docs", lifespan=app_lifespan
)
app.middleware("http")(protect_local_requests)
app.state.pairing = pairing_from_environment()
_manager_lock = threading.Lock()

def get_manager_for_app(target_app: FastAPI) -> ExperimentManager:
    with _manager_lock:
        if not hasattr(target_app.state, "experiment_manager"):
            directory = Path(
                os.environ.get("CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger"))
            )
            target_app.state.experiment_manager = ExperimentManager(
                directory / "experiments.sqlite3"
            )
        return target_app.state.experiment_manager


def get_manager(request: Request) -> ExperimentManager:
    return get_manager_for_app(request.app)

class PairRequest(BaseModel):
    code: str = Field(min_length=9, max_length=9, pattern=r"^[0-9]{9}$")


@app.get("/api/v1/auth/status")
def auth_status(request: Request) -> dict:
    pairing = request.app.state.pairing
    return {
        "enabled": pairing is not None,
        "authenticated": pairing is None or pairing.authorized(
            request.headers.get("authorization")
        ),
    }


@app.post("/api/v1/auth/pair")
def auth_pair(body: PairRequest, request: Request) -> dict:
    pairing = request.app.state.pairing
    if pairing is None:
        raise HTTPException(status_code=409, detail="Pairing is not required")
    token, status = pairing.pair(body.code)
    if token is None:
        if status == "locked":
            raise HTTPException(status_code=429, detail="Too many attempts. Restart the app.")
        raise HTTPException(status_code=403, detail="Invalid, expired or used pairing code")
    return {"token": token, "type": "Bearer", "expires": "when server restarts"}


class ScoreRequest(BaseModel):
    clean_score: float = Field(allow_inf_nan=False)
    corrupted_score: float = Field(allow_inf_nan=False)
    patched_score: float = Field(allow_inf_nan=False)

class MarginRequest(BaseModel):
    correct_logit: float = Field(allow_inf_nan=False)
    incorrect_logit: float = Field(allow_inf_nan=False)

class ExperimentRequest(BaseModel):
    clean: str = Field(min_length=1, max_length=600)
    corrupted: str = Field(min_length=1, max_length=600)
    correct_token: str = Field(min_length=1, max_length=60)
    incorrect_token: str = Field(min_length=1, max_length=60)
    layer: int = Field(ge=0, le=11)
    token_index: int = Field(ge=0, le=127)
    device: Literal["cpu", "mps"] = "cpu"
    revision: str | None = None

    @field_validator("revision")
    @classmethod
    def validate_revision(cls, value: str | None) -> str | None:
        if value is not None and re.fullmatch(r"[0-9a-fA-F]{40}", value) is None:
            raise ValueError("revision must be a 40-character commit SHA")
        return value

    @field_validator("clean", "corrupted")
    @classmethod
    def nonblank_prompt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must not be blank")
        return value

@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "stage": "M12", "version": __version__, "local_only": True}

@app.get("/api/v1/setup")
def setup_status() -> dict:
    """Safe, no-model-load diagnostics for local first-run onboarding."""
    directory = Path(os.environ.get("CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger")))
    existing = next((p for p in (directory, *directory.parents) if p.exists()), Path.home())
    free_gb = round(shutil.disk_usage(existing).free / 1024 ** 3, 1)
    return {
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 11),
        "os": platform.system(),
        "architecture": platform.machine(),
        "torch_installed": importlib.util.find_spec("torch") is not None,
        "transformerlens_installed": importlib.util.find_spec("transformer_lens") is not None,
        "free_disk_gb": free_gb,
        "private_data_default": "local SQLite, no remote sync",
        "model_download_required_first_use": True,
        "isolation": "single worker subprocess",
    }


@app.get("/api/v1/models")
def models(request: Request) -> dict:
    cache = get_manager(request).model_status()
    return {"models": [{"id": "openai-community/gpt2", "status": "supported",
                        "loaded": cache["loaded"], "revision": cache["revision"],
                        "device": cache["device"], "model_loads": cache["model_loads"],
                        "cache_hits": cache["cache_hits"]}]}

@app.post("/api/v1/metrics/margin")
def margin(request: MarginRequest) -> dict:
    return {"margin": logit_margin(request.correct_logit, request.incorrect_logit)}

@app.post("/api/v1/metrics/recovery")
def recovery(request: ScoreRequest) -> dict:
    try:
        return {"recovery": recovery_score(request.clean_score, request.corrupted_score, request.patched_score)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/api/v1/experiments", status_code=202)
def create_experiment(body: ExperimentRequest, request: Request) -> dict:
    try:
        return get_manager(request).submit(body.model_dump(exclude_none=True))
    except QueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

@app.get("/api/v1/experiments")
def list_experiments(request: Request, limit: int = Query(20, ge=1, le=50)) -> dict:
    return {"items": get_manager(request).list_recent(limit)}

@app.get("/api/v1/experiments/{experiment_id}")
def get_experiment(experiment_id: str, request: Request) -> dict:
    if re.fullmatch(r"[0-9a-f]{32}", experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    item = get_manager(request).get(experiment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return item

@app.get("/api/v1/experiments/{experiment_id}/shareable")
def export_shareable(experiment_id: str, request: Request) -> dict:
    if re.fullmatch(r"[0-9a-f]{32}", experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    item = get_manager(request).get(experiment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    try:
        return shareable_report(item)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/api/v1/experiments/{experiment_id}", status_code=204)
def delete_experiment(experiment_id: str, request: Request) -> None:
    if re.fullmatch(r"[0-9a-f]{32}", experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    try:
        get_manager(request).delete(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc
    except NotCancellable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/experiments/{experiment_id}/cancel")
def cancel_experiment(experiment_id: str, request: Request) -> dict:
    if re.fullmatch(r"[0-9a-f]{32}", experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    try:
        get_manager(request).cancel(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc
    except NotCancellable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": experiment_id, "status": "cancelled"}


def mount_built_studio(target_app: FastAPI, web_dir: Path | None = None) -> bool:
    """Serve the compiled local web app; never attempt to serve source files.

    API routes are registered *before* the static catch-all mount.
    There is no external service, public binding or automatic upload.
    """
    location = web_dir or Path(
        os.environ.get(
            "CORTEX_WEB_DIST",
            str(Path(__file__).resolve().parents[1] / "web" / "dist"),
        )
    )
    if not (location / "index.html").is_file():
        return False
    target_app.mount("/", StaticFiles(directory=str(location), html=True), name="studio")
    return True


mount_built_studio(app)
