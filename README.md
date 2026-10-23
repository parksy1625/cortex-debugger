# Cortex Debugger

**Local-first model intervention, visual debugging and automated regression tests**

M3 (v0.4.0-dev) implements a pinned GPT-2 regression verifier on top of
the M2 React studio and FastAPI experiment queue.

## Features

- **Model experiment engine:** clean/corrupted prompt comparison, per-layer
  residual RMS heatmap, single-site activation patch, and self-patch control.
- **M2 GUI:** experiment creation, asynchronous status, metrics, selected heatmap
  cell, local SQLite history and JSON export.
- **M3 regression:** strictly validated versioned JSON manifests,
  `cortex validate`, **live model replay** with `cortex verify`,
  fail-closed threshold assertions and JUnit XML for CI.
- **GitHub Actions:** Python tests, web production build, opt-in model smoke,
  and on-change pinned GPT-2 regression gating.

## Installation

Requires Python >=3.11 and Node >=22 for the UI.

```bash
python -m pip install -e '.[dev,api,ml]'
pytest -q

# Launch local model experiment API
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm install
npm run dev
# http://127.0.0.1:5173
```

The first GPT-2 load downloads model weights. This local API has no
authentication; **never bind it to a public/network interface**.

## M3 regression replay

```bash
cortex validate experiments/regression/gpt2-dog-cat.json

# Rerun pinned GPT-2 and fail CI if comparisons are outside tolerance
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression-report.json \
  --junit artifacts/regression-junit.xml

# Offline JSON check only: does not run model
cortex verify experiments/regression/gpt2-dog-cat.json \
  --artifact artifacts/model-smoke-pair.json
```

Exit status: `0` pass, `1` regression assertion failure, `2` execution
or manifest error. The CLI does not quietly fall back to offline mode.

The sample experiment uses a pinned `openai-community/gpt2` revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`.
The observed model-backed reference is documented in
[docs/MEASURED_RESULTS.md](docs/MEASURED_RESULTS.md), with a
[successful smoke run](https://github.com/parksy1625/cortex-debugger/actions/runs/39992734283).
A successful patch is a **local intervention result**, not a complete
explanation of model reasoning.

See [M3 regression guide](docs/M3_REGRESSION.md),
[M2 UI guide](docs/M2_STUDIO.md) and [known limitations](docs/LIMITATIONS.md).

## Project structure

- `packages/cortex-engine/`: instrumentation, patching and regression assertions
- `apps/api/`: local asynchronous experiment runner and SQLite
- `apps/web/`: React/TypeScript experimental visualization
- `experiments/regression/`: versioned, example-safe CI verification manifests
- `tests/`: unit, integration, error and regression failure tests
- `.github/workflows/`: quality, model smoke and pinned regression replay

MIT License. Contributions welcome.
