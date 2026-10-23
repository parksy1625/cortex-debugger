# M5 — Model reuse, evidence metadata and real-model web E2E

## M5 design

Previously every queued experiment invoked `TransformerBridge.boot_transformers`
independently. That repeated model construction, even if downloaded weight
files were cached on disk. M5 provides a bounded **one-bridge cache** keyed by
`(model_id, exact_revision, device)`, with an RLock spanning cached model
usage. A different revision/device discards the previous model object. This
is **not a bounded RAM allocation**; it retains one entire model in RAM.
To force clean loading, set `CORTEX_DISABLE_MODEL_CACHE=1`.

The local API is designed for **one Python process and one model worker**.
Using `uvicorn --workers 2` would silently break serialized queue
assumptions; do not do that. The model cache is process-local.

`/api/v1/models` shows loaded/not-loaded, device, revision and cache
hit/load counts. Runtime reports include Python, Torch, TransformerLens,
architecture, dtype, seed and whether the bridge was reused. `model_load_seconds`
is measured separately from forward-pass runtime and is **not** total
end-to-end elapsed time.

## Verification matrix

| Test | Backend | Purpose |
| --- | --- | --- |
| Fast `pytest` | Fake model | Cache lifecycle, invalidation, failure, API |
| Real API model test | Pinned GPT-2 | HTTP queue → result, cold → warm reuse |
| Live Chromium E2E | Real localhost API and GPT-2 | Prompt submission, measured heatmap, regression manifest |
| Pinned regression workflow | Pinned GPT-2 | Reproduced activation intervention and 13 assertions |
| Apple MPS smoke (M4) | Real MPS | GPU backend hook behavior |

The real API test is skipped in default fast CI. To execute manually:

```bash
CORTEX_RUN_REAL_MODEL=1 pytest -q -m real_model tests/test_live_model_api.py
```

The live browser test requires the actual Python API and Vite server plus
`CORTEX_LIVE_MODEL=1`; see
[real-model-e2e workflow](../.github/workflows/real-model-e2e.yml).
All workflow results should be checked from GitHub before claiming success.

## Remaining limits

- Cache hit reduces model boot overhead only; no proven aggregate speedup
  until measured on repeated actual runs.
- Model hooks are serialized by the shared cache lock, but safe hard
  cancellation would require a separate process, not an interruptible Python
  thread.
- No complete locked dependency resolution or repeatable multi-platform
  latency benchmark.
- Only one model is retained. Varying revision/device will reload and may
  cause allocator retention on CPU/MPS.
- Raw prompts are transient in the worker; SQLite stores derived token IDs
  and output scores, which can still reveal content.
