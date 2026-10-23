"""M1 paired-prompt residual patching with a TransformerBridge-compatible backend.

Layer/token RMS differences are descriptive. One controlled patch and an
independent identity control measure a localized intervention effect.
"""

from __future__ import annotations

import hashlib
import math
import os
import platform
import time
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from cortex_engine.metrics import logit_margin, recovery_score
from cortex_engine.model_cache import MODEL_CACHE, SingleModelCache
from cortex_engine.validation import validate_pair_lengths, validate_patch_coordinate

MAX_TOKEN_COUNT = 128
DEFAULT_MODEL_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"


def _candidate_id(bridge: Any, candidate: str) -> int:
    if not candidate:
        raise ValueError("Candidate token must not be empty")
    ids = bridge.tokenizer.encode(candidate, add_special_tokens=False)
    if len(ids) != 1:
        raise ValueError(f"Candidate {candidate!r} must encode to exactly one token; got {len(ids)}")
    return int(ids[0])


def _tensor_score(logits: Any, correct_id: int, incorrect_id: int) -> float:
    if logits.ndim != 3 or logits.shape[0] != 1:
        raise ValueError("Expected logits [1, tokens, vocabulary]")
    return logit_margin(
        float(logits[0, -1, correct_id].item()),
        float(logits[0, -1, incorrect_id].item()),
    )


def _cached_residual(cache: Any, site: str, length: int) -> Any:
    if site not in cache:
        raise RuntimeError(f"Missing expected activation hook {site!r}")
    tensor = cache[site]
    if tensor.ndim != 3 or tensor.shape[0] != 1 or tensor.shape[1] != length:
        raise RuntimeError(f"Hook {site} did not return expected shape [1, {length}, hidden]")
    return tensor


def _patch_from(source: Any, index: int):
    """Create a scoped, mutation-safe TransformerLens hook."""
    saved = source[:, index, :].detach().clone()

    def patch(activation: Any, hook: Any = None) -> Any:
        if activation.ndim != 3 or activation.shape[0] != 1 or not 0 <= index < activation.shape[1]:
            raise RuntimeError("Unexpected patch activation tensor shape")
        if activation.shape[-1] != saved.shape[-1]:
            raise RuntimeError("Source/target hidden dimension mismatch")
        out = activation.clone()
        out[:, index, :] = saved.to(device=out.device, dtype=out.dtype)
        return out

    return patch


def analyze_pair(
    bridge: Any,
    *,
    clean: str,
    corrupted: str,
    correct_token: str,
    incorrect_token: str,
    layer: int,
    token_index: int,
    device: str = "cpu",
    model_id: str = "openai-community/gpt2",
    model_revision: str | None = None,
    control_tolerance: float = 1e-4,
) -> dict[str, Any]:
    """Measure one localized activation patch with an independent self-patch control.

    Equal token lengths do not ensure semantic alignment. Call inside inference_mode
    with an eval-mode bridge when using a real PyTorch/TransformerLens model.
    """
    if not (clean.strip() and corrupted.strip()):
        raise ValueError("Both prompts must be nonempty")
    if not math.isfinite(control_tolerance) or control_tolerance <= 0:
        raise ValueError("control_tolerance must be positive and finite")
    clean_tokens = bridge.to_tokens(clean)
    corrupted_tokens = bridge.to_tokens(corrupted)
    if clean_tokens.ndim != 2 or corrupted_tokens.ndim != 2:
        raise ValueError("Expected batched token tensors")
    if clean_tokens.shape[0] != 1 or corrupted_tokens.shape[0] != 1:
        raise ValueError("Batch size must equal one")
    n_clean, n_corrupt = int(clean_tokens.shape[-1]), int(corrupted_tokens.shape[-1])
    validate_pair_lengths(n_clean, n_corrupt, max_tokens=MAX_TOKEN_COUNT)
    n_layers = int(bridge.cfg.n_layers)
    validate_patch_coordinate(layer, token_index, n_layers=n_layers, n_tokens=n_clean)
    correct_id = _candidate_id(bridge, correct_token)
    incorrect_id = _candidate_id(bridge, incorrect_token)
    if correct_id == incorrect_id:
        raise ValueError("Candidate tokens must have different token IDs")
    hook_names = [f"blocks.{i}.hook_out" for i in range(n_layers)]
    start = time.monotonic()

    clean_logits, clean_cache = bridge.run_with_cache(
        clean_tokens, names_filter=lambda name: name in hook_names
    )
    corrupted_logits, corrupted_cache = bridge.run_with_cache(
        corrupted_tokens, names_filter=lambda name: name in hook_names
    )
    differences: list[list[float]] = []
    for hook_name in hook_names:
        source = _cached_residual(clean_cache, hook_name, n_clean)
        target = _cached_residual(corrupted_cache, hook_name, n_corrupt)
        row = ((source.float() - target.float()).square().mean(dim=-1).sqrt())[0]
        differences.append([round(float(value), 6) for value in row.tolist()])
    site = hook_names[layer]
    clean_act = _cached_residual(clean_cache, site, n_clean)
    corrupted_act = _cached_residual(corrupted_cache, site, n_corrupt)
    patched_logits = bridge.run_with_hooks(
        corrupted_tokens, fwd_hooks=[(site, _patch_from(clean_act, token_index))],
        return_type="logits"
    )
    control_logits = bridge.run_with_hooks(
        corrupted_tokens, fwd_hooks=[(site, _patch_from(corrupted_act, token_index))],
        return_type="logits"
    )
    max_control_delta = float((control_logits - corrupted_logits).abs().max().item())
    if not math.isfinite(max_control_delta):
        raise RuntimeError("Identity control has non-finite delta")
    clean_score = _tensor_score(clean_logits, correct_id, incorrect_id)
    corrupted_score = _tensor_score(corrupted_logits, correct_id, incorrect_id)
    patched_score = _tensor_score(patched_logits, correct_id, incorrect_id)
    if not math.isfinite(patched_score):
        raise RuntimeError("Patched logits are not finite")
    return {
        "schema_version": 1,
        "status": "pass" if max_control_delta <= control_tolerance else "fail",
        "model": {"id": model_id, "revision": model_revision, "device": device},
        "input": {
            "clean_sha256": hashlib.sha256(clean.encode()).hexdigest(),
            "corrupted_sha256": hashlib.sha256(corrupted.encode()).hexdigest(),
            "clean_token_ids": clean_tokens[0].tolist(),
            "corrupted_token_ids": corrupted_tokens[0].tolist(),
            "tokens_per_prompt": n_clean,
            "candidate_token_ids": {"correct": correct_id, "incorrect": incorrect_id},
        },
        "patch": {"site": site, "layer": layer, "token_index": token_index},
        "scores": {
            "clean": clean_score, "corrupted": corrupted_score,
            "patched": patched_score,
            "recovery": recovery_score(clean_score, corrupted_score, patched_score),
        },
        "control": {"max_abs_logit_delta": max_control_delta, "tolerance": control_tolerance},
        "activation_rms_delta": differences,
        "runtime_seconds": round(time.monotonic() - start, 3),
        "limitations": [
            "A single patch does not reveal the full model computation.",
            "Activation deltas are descriptive and do not prove causal influence.",
            "Equal token lengths do not guarantee semantic token alignment.",
            "Unpinned model revisions are not suitable for cross-run regression tests."
        ],
    }


def run_gpt2_pair(
    *, clean: str, corrupted: str, correct_token: str, incorrect_token: str,
    layer: int, token_index: int, device: str = "cpu", revision: str | None = None,
) -> dict[str, Any]:
    """Execute paired GPT-2 analysis, downloading weights on first run if needed."""
    if device not in ("cpu", "mps"):
        raise ValueError("Only cpu and mps supported")
    try:
        import torch
        from transformer_lens.model_bridge import TransformerBridge
    except ImportError as exc:
        raise RuntimeError('ML dependencies missing; install pip install -e ".[ml]"') from exc
    torch.manual_seed(0)
    model_id = "openai-community/gpt2"
    revision = revision or DEFAULT_MODEL_REVISION
    cache = SingleModelCache() if os.environ.get("CORTEX_DISABLE_MODEL_CACHE") == "1" else MODEL_CACHE

    # Hold the cache lock throughout inference: TransformerLens hooks must not
    # be modified by concurrent calls that share the same bridge instance.
    with cache.lock:
        bridge, cache_hit, load_seconds = cache.load(
            (model_id, revision, device),
            lambda: TransformerBridge.boot_transformers(
                model_id, device=device, revision=revision
            ),
        )
        with torch.inference_mode():
            result = analyze_pair(
                bridge, clean=clean, corrupted=corrupted,
                correct_token=correct_token, incorrect_token=incorrect_token,
                layer=layer, token_index=token_index, device=device,
                model_id=model_id, model_revision=revision,
            )
    try:
        lens_version = version("transformer-lens")
    except PackageNotFoundError:
        lens_version = "unknown"
    result["execution"] = {
        "python": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "torch": str(torch.__version__),
        "transformer_lens": lens_version,
        "seed": 0,
        "dtype": str(next(iter(bridge.parameters())).dtype)
        if callable(getattr(bridge, "parameters", None)) else "unknown",
        "model_cache_hit": cache_hit,
        "model_load_seconds": load_seconds,
    }
    return result
