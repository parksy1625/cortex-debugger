"""Local-only Cortex API. Start with --host 127.0.0.1, never 0.0.0.0 by default."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cortex_engine import __version__
from cortex_engine.metrics import logit_margin, recovery_score

app = FastAPI(title="Cortex Debugger API", version=__version__, docs_url="/api/docs")


class ScoreRequest(BaseModel):
    clean_score: float = Field(allow_inf_nan=False)
    corrupted_score: float = Field(allow_inf_nan=False)
    patched_score: float = Field(allow_inf_nan=False)


class MarginRequest(BaseModel):
    correct_logit: float = Field(allow_inf_nan=False)
    incorrect_logit: float = Field(allow_inf_nan=False)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "stage": "M0", "version": __version__}


@app.get("/api/v1/models")
def models() -> dict:
    return {"models": [{"id": "openai-community/gpt2", "status": "supported", "loaded": False}]}


@app.post("/api/v1/metrics/margin")
def margin(request: MarginRequest) -> dict:
    return {"margin": logit_margin(request.correct_logit, request.incorrect_logit)}


@app.post("/api/v1/metrics/recovery")
def recovery(request: ScoreRequest) -> dict:
    try:
        return {"recovery": recovery_score(request.clean_score, request.corrupted_score, request.patched_score)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
