"""TransformerLens 4.x reference backend. Model download is explicit via CLI smoke.

No arbitrary model identifiers or trust_remote_code are accepted in v0.1.
"""

from __future__ import annotations

import math
import time

from cortex_engine.validation import validate_pair_lengths, validate_patch_coordinate

MODEL_ID = "openai-community/gpt2"


def self_patch_smoke(
    *, prompt: str = "When Mary went to the store, she bought", device: str = "cpu",
    layer: int = 0, token_index: int = 0
) -> dict:
    """Copy a GPT-2 residual back into the *same* run.

    Verifies hook availability, tensor shape, cleanup, and near-identity numerics.
    This makes no claim about causal recovery on distinct prompts.

    Requires the separately installed `ml` extra. First run downloads model weights.
    """
    if device not in ("cpu", "mps"):
        raise ValueError("v0.1 supports only cpu and mps")
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    try:
        import torch
        from transformer_lens.model_bridge import TransformerBridge
    except ImportError as exc:
        raise RuntimeError('ML dependencies missing; install pip install -e ".[ml]"') from exc

    started = time.monotonic()
    bridge = TransformerBridge.boot_transformers(MODEL_ID, device=device)
    bridge.eval()
    token_ids = bridge.to_tokens(prompt)
    n_tokens = int(token_ids.shape[-1])
    validate_pair_lengths(n_tokens, n_tokens)
    n_layers = int(bridge.cfg.n_layers)
    validate_patch_coordinate(layer, token_index, n_layers=n_layers, n_tokens=n_tokens)
    site = f"blocks.{layer}.hook_out"

    with torch.inference_mode():
        reference_logits, cache = bridge.run_with_cache(
            token_ids, names_filter=lambda name: name == site
        )
        if site not in cache:
            raise RuntimeError(f"Required hook not emitted: {site}")
        source = cache[site][:, token_index, :].detach().clone()

        def patch(activation, hook=None):
            if activation.ndim != 3 or activation.shape[0] != 1:
                raise RuntimeError("Expected residual activation shape [1, tokens, hidden]")
            patched = activation.clone()
            patched[:, token_index, :] = source.to(
                device=patched.device, dtype=patched.dtype
            )
            return patched

        patched_logits = bridge.run_with_hooks(
            token_ids, fwd_hooks=[(site, patch)], return_type="logits"
        )
        max_abs_logit_delta = float((patched_logits - reference_logits).abs().max().item())

    if not math.isfinite(max_abs_logit_delta):
        raise RuntimeError("Self patch produced non-finite logit delta")
    return {
        "schema_version": 1,
        "status": "pass" if max_abs_logit_delta <= 1e-4 else "fail",
        "model_id": MODEL_ID,
        "device": device,
        "layer": layer,
        "token_index": token_index,
        "hook": site,
        "token_count": n_tokens,
        "max_abs_logit_delta": max_abs_logit_delta,
        "tolerance": 1e-4,
        "runtime_seconds": round(time.monotonic() - started, 3),
        "notes": "M0 identity control, not a clean/corrupted causal experiment",
    }
