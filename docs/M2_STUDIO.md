# Cortex Debugger M2 — Local experiment studio

**Status:** M2 integrated API + React experiment UI. Real GPT-2 self-patching and paired-prompt smoke passed in [GitHub Actions run 39992051722](https://github.com/parksy1625/cortex-debugger/actions/runs/39992051722). The 43 Python tests passed locally with a deterministic fake model runner. The frontend TypeScript source syntax was checked; a complete Node dependency build is pending GitHub CI.

## Quick start

```bash
python -m pip install -e '.[api,ml,dev]'
pytest -q
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
# separate terminal:
cd apps/web
npm install
npm run dev
# browser: http://127.0.0.1:5173
```

The first real model run may download model weights. The app only accepts GPT-2, CPU or Apple MPS, prompts ≤600 characters and at most 128 tokens after tokenization. The two token sequences must be equally long and the candidate strings must each encode to one token.

## API

| Endpoint | Behavior |
| --- | --- |
| POST /api/v1/experiments | Validate input, enqueue job, return HTTP 202 + id |
| GET /api/v1/experiments/{id} | Status, safe metadata and result (if finished) |
| GET /api/v1/experiments?limit=20 | Recent 1–50 experiments (no raw prompts) |
| POST /api/v1/experiments/{id}/cancel | Cancel **queued** job; running jobs return 409 |
| GET /api/v1/health | Connectivity + build stage |

Job statuses: queued → running → completed/failed, or queued → cancelled.

## Resource & privacy limits

A single model worker serializes experiments; two additional tasks may wait. Job queue overflow returns HTTP 429. Input text is transient and is not saved in SQLite, but the result **contains token IDs** that can disclose input information. The SQLite file defaults to `~/.cortex-debugger/experiments.sqlite3`, overridable with `CORTEX_DATA_DIR`. Store it locally with appropriate file permissions.

A process restart does not resume previously queued/running jobs. Do not expose this unauthenticated API to other devices. Production work remains: bounded execution time, cancellation of running inference, model caching, revision pinning, persistence retention, secure auditing, and full e2e tests.

Heatmap colors represent RMS residual differences and are **not causal evidence**. A single patched intervention establishes only that this edit altered the measured score under specific conditions. The model identity control must pass before a completed report is treated as usable.

## Still missing

- Real model-backed smoke result from GitHub Actions and macOS MPS.
- React browser/e2e build validation and actual model-run UI walkthrough.
- M3 strict reproducible regression assertion runner; model revision may still be omitted.

## Verified model revision

The default GPT-2 revision is pinned to `607a30d783dfa663caf39e06633721c8d4cfcd7e` based on the official Hugging Face repository metadata. You may override with another exact 40-character commit, but results using different revisions must not be treated as identical baselines. The original smoke sample using an unchanged input token position recovered 0%; the default patch location has been moved to token index 2 for a nontrivial intervention test. Scientific interpretation remains out of scope.
