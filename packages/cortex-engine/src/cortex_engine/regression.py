"""Versioned, fail-closed regression manifests for causal patching experiments.

The default verification mode REPLAYS the pinned model. An explicit artifact mode
checks recorded JSON evidence, but cannot prove the model was rerun.
No arbitrary Python, shell or custom model loaders are accepted from manifests.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from cortex_engine.pairing import DEFAULT_MODEL_REVISION

SUPPORTED_MODEL = "openai-community/gpt2"
MAX_MANIFEST_BYTES = 65_536
MAX_ARTIFACT_BYTES = 5_242_880
METRIC_KEYS = frozenset({
    "control_delta_max", "recovery_min", "recovery_max",
    "patched_margin_min", "patched_margin_max",
})


def _read_json(path: str | Path, limit: int) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file() or target.stat().st_size > limit:
        raise ValueError(f"JSON file missing or exceeds {limit} bytes: {target}")
    try:
        data = json.loads(target.read_text(encoding="utf-8"), parse_constant=_invalid_number)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {target}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _invalid_number(value: str) -> None:
    raise ValueError(f"Non-finite JSON literal {value} is forbidden")


def _keys(value: Any, required: set[str], allowed: set[str], name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing or unknown:
        raise ValueError(f"{name} invalid keys (missing={sorted(missing)}, unknown={sorted(unknown)})")
    return value


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Return validated (unmodified) manifest; fail on unknown fields/schema versions."""
    _keys(data, {"schema_version", "model", "experiment", "assertions"},
          {"schema_version", "model", "experiment", "assertions"}, "manifest")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Only schema_version=1 is supported")
    model = _keys(data["model"], {"id", "revision", "device"},
                  {"id", "revision", "device"}, "model")
    if model["id"] != SUPPORTED_MODEL:
        raise ValueError("Only openai-community/gpt2 is allowed")
    if not isinstance(model["revision"], str) or not re.fullmatch(r"[0-9a-f]{40}", model["revision"]):
        raise ValueError("model.revision must be a pinned 40-character lowercase SHA")
    if model["revision"] != DEFAULT_MODEL_REVISION:
        # Explicit override could be supported later once a new baseline is measured.
        raise ValueError("Model revision differs from the validated GPT-2 baseline")
    if model["device"] not in ("cpu", "mps"):
        raise ValueError("model.device must be cpu or mps")
    exp_keys = {"clean", "corrupted", "correct_token", "incorrect_token", "layer", "token_index"}
    exp = _keys(data["experiment"], exp_keys, exp_keys, "experiment")
    for key in ("clean", "corrupted"):
        value = exp[key]
        if not isinstance(value, str) or not value.strip() or len(value) > 600:
            raise ValueError(f"experiment.{key} must be non-empty text of at most 600 characters")
    if exp["clean"] == exp["corrupted"]:
        raise ValueError("Clean and corrupted prompts must differ")
    for key in ("correct_token", "incorrect_token"):
        value = exp[key]
        if not isinstance(value, str) or not value or len(value) > 60:
            raise ValueError(f"experiment.{key} must be 1–60 characters")
    if exp["correct_token"] == exp["incorrect_token"]:
        raise ValueError("Candidate tokens must differ")
    for key, high in (("layer", 11), ("token_index", 127)):
        value = exp[key]
        if type(value) is not int or not 0 <= value <= high:
            raise ValueError(f"experiment.{key} must be an integer in [0, {high}]")

    constraints = _keys(data["assertions"], {"control_delta_max"},
                        set(METRIC_KEYS), "assertions")
    if len(constraints) < 2:
        raise ValueError("At least one model-behavior assertion is required")
    for key, value in constraints.items():
        _finite(value, f"assertions.{key}")
    if not 0 < constraints["control_delta_max"] <= 0.1:
        raise ValueError("control_delta_max must lie in (0, 0.1]")
    for name in ("recovery", "patched_margin"):
        lower, upper = name + "_min", name + "_max"
        if lower in constraints and upper in constraints and constraints[lower] > constraints[upper]:
            raise ValueError(f"{lower} must be <= {upper}")
    return data


def load_manifest(path: str | Path) -> dict[str, Any]:
    return validate_manifest(_read_json(path, MAX_MANIFEST_BYTES))


def _matching_evidence(manifest: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Treat mismatching evidence metadata as hard assertion failures."""
    model, exp = manifest["model"], manifest["experiment"]
    observed_model = evidence.get("model") or {}
    observed_patch = evidence.get("patch") or {}
    observed_inputs = evidence.get("input") or {}
    pairs = {
        "model_id": (observed_model.get("id"), model["id"]),
        "model_revision": (observed_model.get("revision"), model["revision"]),
        "device": (observed_model.get("device"), model["device"]),
        "patch_layer": (observed_patch.get("layer"), exp["layer"]),
        "patch_token": (observed_patch.get("token_index"), exp["token_index"]),
        "clean_sha256": (observed_inputs.get("clean_sha256"), hashlib.sha256(exp["clean"].encode()).hexdigest()),
        "corrupted_sha256": (observed_inputs.get("corrupted_sha256"), hashlib.sha256(exp["corrupted"].encode()).hexdigest()),
    }
    return [{"name": name, "passed": measured == expected, "observed": measured,
             "expected": expected} for name, (measured, expected) in pairs.items()]


def evaluate(manifest: dict[str, Any], evidence: dict[str, Any], *, mode: str) -> dict[str, Any]:
    """Check all claims against metadata AND numeric assertions, even when one fails."""
    validate_manifest(manifest)
    if mode not in ("replay", "artifact"):
        raise ValueError("Verification mode must be replay or artifact")
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 1:
        raise ValueError("Unsupported or invalid experiment result schema")
    checks = _matching_evidence(manifest, evidence)
    checks.append({"name": "engine_status", "passed": evidence.get("status") == "pass",
                   "observed": evidence.get("status"), "expected": "pass"})

    control, scores = evidence.get("control"), evidence.get("scores")
    if not isinstance(control, dict) or not isinstance(scores, dict):
        raise ValueError("Experiment evidence missing control/scores sections")
    limits = manifest["assertions"]
    measured: dict[str, float | None] = {}
    for key in ("control_delta_max", "recovery_min", "recovery_max",
                "patched_margin_min", "patched_margin_max"):
        if key not in limits:
            continue
        source = control.get("max_abs_logit_delta") if key == "control_delta_max" else (
            scores.get("recovery") if key.startswith("recovery") else scores.get("patched")
        )
        try:
            measured[key] = _finite(source, key)
        except ValueError:
            measured[key] = None
        val = measured[key]
        passed = val is not None and (val >= limits[key] if key.endswith("_min") else val <= limits[key])
        checks.append({"name": key, "passed": passed, "observed": val, "expected": limits[key]})
    ok = all(item["passed"] for item in checks)
    return {"schema_version": 1, "status": "pass" if ok else "fail", "mode": mode,
            "model_revision": manifest["model"]["revision"],
            "checks": checks, "passed": sum(item["passed"] for item in checks),
            "failed": sum(not item["passed"] for item in checks),
            "warning": ("Checked a saved artifact only; no model was rerun."
                        if mode == "artifact" else "Pinned model was rerun.")}


def write_json(path: str | Path, result: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                      encoding="utf-8")


def write_junit(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suite = ET.Element("testsuite", name="cortex.regression",
                       tests=str(len(report["checks"])), failures=str(report["failed"]),
                       errors="0")
    for check in report["checks"]:
        item = ET.SubElement(suite, "testcase", classname="cortex.regression",
                             name=check["name"])
        if not check["passed"]:
            failure = ET.SubElement(item, "failure", message="Regression assertion failed")
            failure.text = (f"Observed {check.get('observed')!r}; "
                            f"expected {check.get('expected')!r}")
    ET.ElementTree(suite).write(target, encoding="utf-8", xml_declaration=True)


def verify(manifest: dict[str, Any], *, artifact_path: str | Path | None = None) -> dict[str, Any]:
    validate_manifest(manifest)
    if artifact_path is not None:
        result = _read_json(artifact_path, MAX_ARTIFACT_BYTES)
        return evaluate(manifest, result, mode="artifact")
    from cortex_engine.pairing import run_gpt2_pair

    model, exp = manifest["model"], manifest["experiment"]
    result = run_gpt2_pair(**exp, device=model["device"], revision=model["revision"])
    return evaluate(manifest, result, mode="replay")
