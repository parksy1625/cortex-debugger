# M5 verification report — 2026-10-24 KST

## Verified GitHub Actions

- [Quality checks #40000365809](https://github.com/parksy1625/cortex-debugger/actions/runs/40000365809): **PASS** — 81 Python tests passed, 1 real-model opt-in test skipped, Ruff passed, React production build passed. Source commit `1095cfa7`.
- [Real-model API and browser E2E #40000365940](https://github.com/parksy1625/cortex-debugger/actions/runs/40000365940): **PASS** on source commit `1095cfa7`.
  - Real pinned GPT-2 experiment issued through FastAPI TestClient: 1 integration test passed. It submitted **two sequential actual model inference jobs**, asserted first bridge cache miss and second bridge cache hit, and checked results and API model cache status.
  - React/Vite + FastAPI/GPT-2 + Chromium: 1 real model browser E2E test passed, including a complete experiment, real output and regression-manifest export.
- [Pinned model regression #40000058346](https://github.com/parksy1625/cortex-debugger/actions/runs/40000058346): earlier M5 model-engine source commit passed pinned replay. Check [latest regression workflow](https://github.com/parksy1625/cortex-debugger/actions/workflows/regression.yml) for the most recent run.

## What has improved

The API uses `SingleModelCache` keyed by `(model id, exact revision, device)`. On a cache hit it does not call TransformerLens model boot again. A lock spans model usage to prevent simultaneous hook work on the same instance. On switching model configurations, previous cache entries are discarded and the new bridge loads.

Experiment JSON evidence additionally records: Python runtime version, PyTorch version, TransformerLens version, OS/architecture, seed, dtype, `model_cache_hit`, and `model_load_seconds`.

The separate `/api/v1/models` endpoint exposes whether a model is loaded and load/hit counts, not prompts.

## Interpretation

The test proves one pinned model was **reused**, not that end-to-end throughput or memory use improved by a particular factor. No cold/warm wall-clock benchmark was recorded in this version. Actual activation computations are still performed for each experiment.

The real browser E2E test uses the genuine Python and GPT-2 backend rather than a mocked response, extending coverage beyond M4's three simulated API browser tests.

## Important limitations

- Model bridge is held in process RAM until replaced or the process exits. This **increases baseline memory usage** while the server is idle.
- PyTorch execution is still in one Python thread. A running task cannot be safely interrupted or killed; enforceable timeouts need process-level isolation.
- Multiple Uvicorn workers are unsupported, and remote/public API binding would be unsafe.
- No full dependency lockfile, signed execution provenance, robust benchmark distribution, or multi-model adapter validation.
- Raw prompts in exported regression manifests must not be shared publicly.
