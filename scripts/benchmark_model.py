"""Reproducible smoke benchmark for pinned GPT-2 through isolated worker.

Measures wall time across one cold and multiple warm model experiments.
This is one runner/sample, not a generalized CPU or MPS benchmark.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import threading
import time
from pathlib import Path

from apps.api.model_process import ModelProcess
from cortex_engine.pairing import DEFAULT_MODEL_REVISION

INPUTS = {
    "clean": "The dog runs",
    "corrupted": "The cat runs",
    "correct_token": " dog",
    "incorrect_token": " cat",
    "layer": 5,
    "token_index": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure repeated pinned GPT-2 experiments")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--output", type=Path, default=Path("artifacts/m7-benchmark.json"))
    args = parser.parse_args()
    if not 2 <= args.runs <= 10:
        parser.error("--runs must be between 2 and 10")
    samples = []
    worker = ModelProcess(timeout_seconds=args.timeout)
    try:
        for i in range(args.runs):
            started = time.monotonic()
            result = worker.execute(
                {**INPUTS, "device": args.device, "revision": DEFAULT_MODEL_REVISION},
                threading.Event(),
            )
            elapsed = time.monotonic() - started
            if result.get("status") != "pass":
                raise RuntimeError("Identity control failed; benchmark invalid")
            execution = result.get("execution") or {}
            warm = bool(execution.get("model_cache_hit"))
            if warm != (i > 0):
                raise RuntimeError("Unexpected model cache behavior; benchmark invalid")
            samples.append({
                "number": i + 1,
                "wall_seconds": round(elapsed, 4),
                "cache_hit": warm,
                "model_load_seconds": execution.get("model_load_seconds"),
                "model_forward_seconds": result.get("runtime_seconds"),
                "recovery": result.get("scores", {}).get("recovery"),
            })
        status = worker.status()
    finally:
        worker.stop()
    warm_median = statistics.median(sample["wall_seconds"] for sample in samples[1:])
    report = {
        "schema_version": 1,
        "name": "single-runner-gpt2-cold-warm",
        "model_id": "openai-community/gpt2",
        "model_revision": DEFAULT_MODEL_REVISION,
        "device": args.device,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "runs": samples,
        "cold_wall_seconds": samples[0]["wall_seconds"],
        "warm_median_wall_seconds": warm_median,
        "observed_cold_to_warm_ratio": round(samples[0]["wall_seconds"] / warm_median, 3)
        if warm_median > 0 else None,
        "sampled_peak_worker_rss_mb": status["sampled_peak_worker_rss_mb"],
        "warning": "One hardware run, includes first model load; not an isolated throughput claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
