"""Synthetic Bridge-compatible tests: no model download or TransformerLens required."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import torch
from cortex_engine.pairing import analyze_pair


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        table = {" yes": [1], " no": [2], " multi": [1, 2], " identical": [1]}
        return table.get(text, [])


@dataclass
class Config:
    n_layers: int = 3


class FakeBridge:
    cfg = Config()
    tokenizer = FakeTokenizer()

    def to_tokens(self, text):
        return torch.tensor([[ord(c) % 16 for c in text]], dtype=torch.long)

    def _activation(self, tokens, layer):
        return (tokens.float() * (layer + 1)).unsqueeze(-1).repeat(1, 1, 4)

    def _logits(self, tokens, modified=None):
        hidden = modified if modified is not None else self._activation(tokens, 1)
        summed = hidden[:, -1, :].sum(dim=-1)
        logits = torch.zeros((1, tokens.shape[-1], 16), dtype=torch.float32)
        logits[:, -1, 1] = summed
        logits[:, -1, 2] = -summed
        return logits

    def run_with_cache(self, tokens, names_filter):
        cache = {}
        for layer in range(self.cfg.n_layers):
            name = f"blocks.{layer}.hook_out"
            if names_filter(name):
                cache[name] = self._activation(tokens, layer)
        return self._logits(tokens), cache

    def run_with_hooks(self, tokens, fwd_hooks, return_type):
        name, callback = fwd_hooks[0]
        layer = int(name.split(".")[1])
        original = self._activation(tokens, layer)
        modified = callback(original, None)
        if layer == 1:
            return self._logits(tokens, modified=modified)
        return self._logits(tokens)


DATA = dict(
    clean="abca", corrupted="abcb", correct_token=" yes",
    incorrect_token=" no", layer=1, token_index=3,
)


def test_pair_metric_shape_and_control():
    result = analyze_pair(FakeBridge(), **DATA)
    assert result["status"] == "pass"
    assert result["scores"]["recovery"] == pytest.approx(1.0)
    assert result["control"]["max_abs_logit_delta"] == 0
    assert len(result["activation_rms_delta"]) == 3
    assert len(result["activation_rms_delta"][0]) == 4
    assert result["input"]["clean_sha256"] != result["input"]["corrupted_sha256"]


def test_pair_no_measurable_recovery_when_patch_earlier_token():
    result = analyze_pair(FakeBridge(), **{**DATA, "token_index": 0})
    assert result["scores"]["recovery"] == pytest.approx(0.0)


@pytest.mark.parametrize("changed", [
    {"clean": "a"},
    {"correct_token": " multi"},
    {"incorrect_token": " identical"},
    {"layer": 7},
    {"token_index": -1},
    {"clean": ""},
])
def test_invalid_pair_inputs(changed):
    with pytest.raises(ValueError):
        analyze_pair(FakeBridge(), **{**DATA, **changed})


def test_control_failure_is_reported_not_hidden():
    class BrokenBridge(FakeBridge):
        def run_with_hooks(self, tokens, fwd_hooks, return_type):
            logits = super().run_with_hooks(tokens, fwd_hooks, return_type)
            logits[:, -1, 0] = 1
            return logits

    output = analyze_pair(BrokenBridge(), **DATA)
    assert output["status"] == "fail"
    assert output["control"]["max_abs_logit_delta"] == 1.0
