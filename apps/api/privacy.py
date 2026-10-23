"""Privacy-conscious exports for local Cortex reports.

Only explicitly allowlisted aggregate model measurements are exported.
No raw prompts, prompt hashes, input token IDs, candidate IDs, job IDs,
filesystem paths, model error strings or full execution environment details.
An aggregate score may still be sensitive if a user knows the experiment.
"""

from __future__ import annotations

import math
from typing import Any


def _finite_number(value: Any) -> float | None:
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    return float(value)


def shareable_report(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("status") != "completed" or not isinstance(record.get("result"), dict):
        raise ValueError("Only completed experiments can be shared")
    result = record["result"]
    model, scores, patch, control = (
        result.get("model"), result.get("scores"),
        result.get("patch"), result.get("control"),
    )
    if not all(isinstance(item, dict) for item in (model, scores, patch, control)):
        raise ValueError("Incomplete experiment evidence")
    if result.get("status") != "pass":
        raise ValueError("Experiment did not pass the identity control")
    metrics = {
        "clean_margin": _finite_number(scores.get("clean")),
        "corrupted_margin": _finite_number(scores.get("corrupted")),
        "patched_margin": _finite_number(scores.get("patched")),
        "recovery": _finite_number(scores.get("recovery")),
        "identity_control_delta": _finite_number(control.get("max_abs_logit_delta")),
    }
    if any(metrics[key] is None for key in (
        "clean_margin", "corrupted_margin", "patched_margin", "identity_control_delta"
    )):
        raise ValueError("Non-finite or missing experiment metrics")
    for name in ("layer", "token_index"):
        if type(patch.get(name)) is not int or patch[name] < 0:
            raise ValueError("Invalid patch location")
    return {
        "schema_version": 1,
        "kind": "cortex-redacted-summary",
        "redacted": True,
        "warning": "Aggregated metrics may still reveal sensitive facts; review before sharing.",
        "model": {
            "id": str(model.get("id", ""))[:100],
            "revision": str(model.get("revision", ""))[:40],
            "device": str(model.get("device", ""))[:16],
        },
        "patch": {"layer": patch["layer"], "token_index": patch["token_index"]},
        "scores": metrics,
        "note": "This redacted summary cannot be used for exact experiment replay.",
    }
