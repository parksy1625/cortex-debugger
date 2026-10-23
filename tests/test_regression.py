"""M3 regression validation, replay dispatch and negative assertion tests (no weights)."""

from __future__ import annotations

import hashlib
import json
from xml.etree import ElementTree

import pytest

from cortex_engine.cli import main
from cortex_engine.regression import (
    evaluate,
    load_manifest,
    validate_manifest,
    verify,
    write_json,
    write_junit,
)

PIN = "607a30d783dfa663caf39e06633721c8d4cfcd7e"


@pytest.fixture
def manifest():
    return {
        "schema_version": 1,
        "model": {"id": "openai-community/gpt2", "revision": PIN, "device": "cpu"},
        "experiment": {
            "clean": "The dog runs", "corrupted": "The cat runs",
            "correct_token": " dog", "incorrect_token": " cat",
            "layer": 5, "token_index": 2,
        },
        "assertions": {
            "control_delta_max": 0.0001, "recovery_min": 0.75,
            "recovery_max": 1.35, "patched_margin_min": 0.55,
            "patched_margin_max": 1.15,
        },
    }


@pytest.fixture
def evidence(manifest):
    exp = manifest["experiment"]
    return {
        "schema_version": 1, "status": "pass",
        "model": manifest["model"].copy(),
        "patch": {"layer": 5, "token_index": 2},
        "input": {
            "clean_sha256": hashlib.sha256(exp["clean"].encode()).hexdigest(),
            "corrupted_sha256": hashlib.sha256(exp["corrupted"].encode()).hexdigest(),
        },
        "control": {"max_abs_logit_delta": 0, "tolerance": 0.0001},
        "scores": {
            "clean": 0.8115386963, "corrupted": -0.3125610352,
            "patched": 0.8504791260, "recovery": 1.0346414367,
        },
    }


def test_valid_manifest(manifest, tmp_path):
    path = tmp_path / "manifest.json"
    write_json(path, manifest)
    assert load_manifest(path) == manifest


@pytest.mark.parametrize("corruption", [
    lambda m: m.update(schema_version=2),
    lambda m: m["model"].update(revision="main"),
    lambda m: m["model"].update(revision="f" * 40),
    lambda m: m["model"].update(id="random/model"),
    lambda m: m["model"].update(device="cuda"),
    lambda m: m["experiment"].update(token_index=128),
    lambda m: m["experiment"].update(layer=True),
    lambda m: m["experiment"].update(clean=m["experiment"]["corrupted"]),
    lambda m: m["experiment"].update(correct_token=m["experiment"]["incorrect_token"]),
    lambda m: m["assertions"].update(recovery_min=1.5),
    lambda m: m["assertions"].update(control_delta_max=float("nan")),
    lambda m: m["assertions"].update(unknown_metric=4),
    lambda m: m.update(extra="ignored"),
])
def test_reject_manifest_corruption(manifest, corruption):
    corruption(manifest)
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_accept_measured_evidence(manifest, evidence):
    report = evaluate(manifest, evidence, mode="artifact")
    assert report["status"] == "pass"
    assert report["failed"] == 0
    assert report["mode"] == "artifact"
    assert "no model was rerun" in report["warning"]


@pytest.mark.parametrize("path,value", [
    (("model", "revision"), "f" * 40),
    (("model", "device"), "mps"),
    (("patch", "layer"), 4),
    (("patch", "token_index"), 1),
    (("input", "clean_sha256"), "0" * 64),
    (("input", "corrupted_sha256"), "0" * 64),
    (("scores", "recovery"), 0.1),
    (("scores", "patched"), -2.0),
    (("control", "max_abs_logit_delta"), 0.25),
])
def test_evidence_mismatch_fails(manifest, evidence, path, value):
    evidence[path[0]][path[1]] = value
    report = evaluate(manifest, evidence, mode="artifact")
    assert report["status"] == "fail"
    assert report["failed"] >= 1


def test_engine_failure_fails(manifest, evidence):
    evidence["status"] = "fail"
    assert evaluate(manifest, evidence, mode="artifact")["status"] == "fail"


def test_undefined_recovery_fails_when_bounded(manifest, evidence):
    evidence["scores"]["recovery"] = None
    assert evaluate(manifest, evidence, mode="artifact")["status"] == "fail"


def test_junit_reports_failures(manifest, evidence, tmp_path):
    evidence["scores"]["recovery"] = 0
    report = evaluate(manifest, evidence, mode="artifact")
    path = tmp_path / "out.xml"
    write_junit(path, report)
    root = ElementTree.parse(path).getroot()
    assert root.tag == "testsuite"
    assert int(root.attrib["failures"]) >= 1
    assert root.find(".//failure") is not None


def test_artifact_is_not_rerun(manifest, evidence, tmp_path, monkeypatch):
    path = tmp_path / "evidence.json"
    write_json(path, evidence)

    def explode(**_kwargs):
        raise AssertionError("model must not be called")

    monkeypatch.setattr("cortex_engine.pairing.run_gpt2_pair", explode)
    report = verify(manifest, artifact_path=path)
    assert report["mode"] == "artifact"
    assert report["status"] == "pass"


def test_replay_invokes_pinned_model(manifest, evidence, monkeypatch):
    calls = []

    def fake_model(**kwargs):
        calls.append(kwargs)
        return evidence

    monkeypatch.setattr("cortex_engine.pairing.run_gpt2_pair", fake_model)
    report = verify(manifest)
    assert report["mode"] == "replay"
    assert report["status"] == "pass"
    assert calls[0]["revision"] == PIN
    assert calls[0]["layer"] == 5


def test_cli_verify_exit_statuses(manifest, evidence, tmp_path, capsys):
    spec = tmp_path / "spec.json"
    artifact = tmp_path / "evidence.json"
    report = tmp_path / "report.json"
    junit = tmp_path / "report.xml"
    write_json(spec, manifest)
    write_json(artifact, evidence)
    assert main(["validate", str(spec)]) == 0
    assert main(["verify", str(spec), "--artifact", str(artifact),
                 "--report", str(report), "--junit", str(junit)]) == 0
    assert json.loads(report.read_text())["status"] == "pass"
    assert junit.is_file()
    evidence["scores"]["recovery"] = -4.0
    write_json(artifact, evidence)
    assert main(["verify", str(spec), "--artifact", str(artifact)]) == 1
    evidence["schema_version"] = 3
    write_json(artifact, evidence)
    assert main(["verify", str(spec), "--artifact", str(artifact)]) == 2
    assert '"status": "error"' in capsys.readouterr().err


def test_reject_malformed_files(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text('{"schema_version":NaN}')
    with pytest.raises(ValueError):
        load_manifest(f)
    f.write_text("{" + " " * 66000 + "}")
    with pytest.raises(ValueError):
        load_manifest(f)


def test_zero_behaviour_assertions_rejected(manifest):
    manifest["assertions"] = {"control_delta_max": 0.0001}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_no_prompt_leakage_into_report(manifest, evidence):
    report = evaluate(manifest, evidence, mode="replay")
    assert manifest["experiment"]["clean"] not in json.dumps(report)
