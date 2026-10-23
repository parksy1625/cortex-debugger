"""M5 single-model cache: no model download, mock model lifecycle."""

from __future__ import annotations

import sys
from types import ModuleType

import torch
from cortex_engine.model_cache import SingleModelCache


class DummyBridge:
    def __init__(self):
        self.eval_count = 0

    def eval(self):
        self.eval_count += 1
        return self

    def parameters(self):
        yield torch.nn.Parameter(torch.ones(1))


def test_cache_hit_and_model_identity():
    cache = SingleModelCache()
    created = []

    def factory():
        model = DummyBridge()
        created.append(model)
        return model

    first, hit1, duration1 = cache.load(("gpt2", "sha-a", "cpu"), factory)
    second, hit2, duration2 = cache.load(("gpt2", "sha-a", "cpu"), factory)
    assert first is second
    assert [hit1, hit2] == [False, True]
    assert duration1 >= 0
    assert duration2 == 0
    assert len(created) == 1
    assert first.eval_count == 1
    assert cache.status()["model_loads"] == 1
    assert cache.status()["cache_hits"] == 1
    assert cache.status()["revision"] == "sha-a"


def test_device_or_revision_change_replaces_previous_model():
    cache = SingleModelCache()
    models = []
    def factory():
        bridge = DummyBridge()
        models.append(bridge)
        return bridge

    cache.load(("gpt2", "sha-a", "cpu"), factory)
    cache.load(("gpt2", "sha-a", "mps"), factory)
    cache.load(("gpt2", "sha-b", "mps"), factory)
    assert len(models) == 3
    assert cache.status()["model_loads"] == 3
    assert cache.status()["device"] == "mps"
    assert cache.status()["revision"] == "sha-b"
    cache.clear()
    assert cache.status()["loaded"] is False
    assert cache.status()["revision"] is None


def test_failed_load_does_not_keep_stale_model():
    cache = SingleModelCache()
    cache.load(("gpt2", "sha-a", "cpu"), DummyBridge)

    def broken():
        raise RuntimeError("model load unavailable")

    import pytest
    with pytest.raises(RuntimeError, match="unavailable"):
        cache.load(("gpt2", "sha-b", "cpu"), broken)
    assert cache.status()["loaded"] is False
    assert cache.status()["model_id"] is None


def test_pair_runner_reuses_loaded_bridge(monkeypatch):
    from cortex_engine import pairing

    # Fake TransformerLens entrypoint but real PyTorch inference_mode.
    class DummyTransformerBridge:
        boot_calls = 0

        @classmethod
        def boot_transformers(cls, model_id, *, device, revision):
            cls.boot_calls += 1
            return DummyBridge()

    fake_pkg = ModuleType("transformer_lens")
    fake_module = ModuleType("transformer_lens.model_bridge")
    fake_module.TransformerBridge = DummyTransformerBridge
    monkeypatch.setitem(sys.modules, "transformer_lens", fake_pkg)
    monkeypatch.setitem(sys.modules, "transformer_lens.model_bridge", fake_module)
    monkeypatch.setattr(pairing, "MODEL_CACHE", SingleModelCache())
    monkeypatch.delenv("CORTEX_DISABLE_MODEL_CACHE", raising=False)

    def mock_analyze(_bridge, **kwargs):
        assert kwargs["model_revision"] in (pairing.DEFAULT_MODEL_REVISION, "e" * 40)
        return {"status": "pass", "scores": {"recovery": 0.5}}

    monkeypatch.setattr(pairing, "analyze_pair", mock_analyze)
    kwargs = dict(clean="a", corrupted="b", correct_token=" yes",
                  incorrect_token=" no", layer=0, token_index=0)
    first = pairing.run_gpt2_pair(**kwargs)
    second = pairing.run_gpt2_pair(**kwargs)
    assert first["execution"]["model_cache_hit"] is False
    assert second["execution"]["model_cache_hit"] is True
    assert second["execution"]["model_load_seconds"] == 0
    assert first["execution"]["seed"] == 0
    assert first["execution"]["torch"] == str(torch.__version__)
    assert first["execution"]["dtype"] == "torch.float32"
    assert DummyTransformerBridge.boot_calls == 1
    # A new revision forces a new bridge, never mixes existing activations.
    pairing.run_gpt2_pair(**kwargs, revision="e" * 40)
    assert DummyTransformerBridge.boot_calls == 2
    # Cache disable is explicit and creates a fresh model each time.
    monkeypatch.setenv("CORTEX_DISABLE_MODEL_CACHE", "1")
    no_cache = pairing.run_gpt2_pair(**kwargs)
    assert no_cache["execution"]["model_cache_hit"] is False
    assert DummyTransformerBridge.boot_calls == 3
