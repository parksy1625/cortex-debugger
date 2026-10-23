# Cortex Debugger

Local-first AI model debugger: activation patching, browser investigation, and
**replayable causal regression testing**.

## M5 · v0.6.0-dev

- **Single-process model reuse** for consecutive experiments with the same
  model/revision/device. One model is held in RAM; switching configuration
  evicts the previous instance. Hook operations are serialized.
- Explicit model cache status in `GET /api/v1/models` (load count, hit count,
  revision, device). Set `CORTEX_DISABLE_MODEL_CACHE=1` to opt out.
- More reproducible evidence: Python, PyTorch and TransformerLens versions,
  OS/architecture, seed, dtype, cache status, and model load duration recorded.
- **Real-model HTTP API + browser** integration checks in GitHub Actions, in
  addition to fast API simulations and unit tests.
- M4 features retained: React layer×token map, hash-checked regression
  manifest exporter, SQLite history, bounded experiment queue, strict
  `cortex verify` with nonzero CI failure and JUnit XML.

## Set up (localhost only)

```bash
python -m pip install -e '.[dev,api,ml]'
pytest -q
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In another shell:

```bash
cd apps/web
npm install
npm run dev
# http://127.0.0.1:5173
```

GPT-2 weights are downloaded on first use. Do not expose the API publicly;
it has **no authentication**, rate limiting for hostile environments, or
per-request process isolation.

## Real-model end-to-end tests

Separate GitHub workflow: [Real-model API and browser E2E](.github/workflows/real-model-e2e.yml).
The workflow validates the FastAPI job queue with **two actual GPT-2 runs**,
checks cache miss → hit, starts the local API, and drives a real model
experiment from the Chromium browser. It is intentionally heavier than the
mocked browser tests; its current status must be checked in GitHub Actions.

```bash
CORTEX_RUN_REAL_MODEL=1 pytest -q -m real_model tests/test_live_model_api.py

# With API + Vite running:
cd apps/web
CORTEX_LIVE_MODEL=1 npx playwright test tests/live-model.spec.ts
```

## Regression replay

```bash
cortex validate experiments/regression/gpt2-dog-cat.json
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression.json --junit artifacts/regression.xml
```

`cortex verify --artifact FILE` checks existing JSON only and **does not**
rerun a model. A regression manifest contains raw prompts: never publish
confidential input. The one recorded dog/cat experiment is a mechanical smoke
example, **not** a comprehensive causal explanation of GPT-2.

## Evidence and limitations

- [M4 verified CPU/MPS model results](docs/M4_VALIDATION.md)
- [M3 pinned GPT-2 replay validation](docs/M3_VALIDATION.md)
- [M5 performance and integration design](docs/M5_STABILITY.md)
- [Known limitations](docs/LIMITATIONS.md)

**M5 real-model validation passed:** [81 Python tests and React build](https://github.com/parksy1625/cortex-debugger/actions/runs/40000365809), [real FastAPI two-run cache test and live Chromium E2E](https://github.com/parksy1625/cortex-debugger/actions/runs/40000365940). See [M5 validation report](docs/M5_VALIDATION.md).\n\nModel cache reuse was confirmed, but no end-to-end speedup factor has been established. The cache skips repeated model loading; activation-patching forward passes remain.

MIT License.
