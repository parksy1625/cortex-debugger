"""Local-only Cortex API. Bind to 127.0.0.1; do not expose unauthenticated endpoints."""
from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Literal

from cortex_engine import __version__
from cortex_engine.metrics import logit_margin, recovery_score
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from apps.api.experiments import ExperimentManager, NotCancellable, QueueFull

app = FastAPI(title="Cortex Debugger API", version=__version__, docs_url="/api/docs")
_manager_lock = threading.Lock()

def get_manager(request: Request) -> ExperimentManager:
    with _manager_lock:
        if not hasattr(request.app.state, "experiment_manager"):
            directory = Path(os.environ.get("CORTEX_DATA_DIR", str(Path.home() / ".cortex-debugger")))
            request.app.state.experiment_manager = ExperimentManager(directory / "experiments.sqlite3")
        return request.app.state.experiment_manager

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
    return {"status": "ok", "stage": "M7", "version": __version__, "local_only": True}

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
