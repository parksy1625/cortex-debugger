# Cortex Debugger

**Open-source model intervention and AI regression testing workbench.**

M4 (v0.5.0-dev) builds on a measured GPT-2 activation-patching engine and
strict CLI regression verifier with a local browser experiment studio.

## What works

- Paired clean/corrupted prompt residual activation patching in GPT-2.
- A layer×token activation RMS map, logit-margin scoring and self-patch control.
- Local FastAPI bounded experiment queue, SQLite history, JSON evidence export.
- Pinned-model `cortex verify` replay and a 13-assertion CI regression gate.
- Browser-based regression manifest authoring: verify input hashes, model
  revision and patch metadata, review numeric ranges, download versioned JSON.
- Browser E2E checks with a mocked API, and a job-restart recovery guard.

## Verified evidence

- [Real-model pinned GPT-2 regression](https://github.com/parksy1625/cortex-debugger/actions/runs/39994357934): **13/13 checks passed**, source revision pinned.
- [Previous quality CI](https://github.com/parksy1625/cortex-debugger/actions/runs/39994490378): 76 Python tests and React production build passed.
- [M3 validation details](docs/M3_VALIDATION.md).

**M4 independent validation passed:** [3/3 Chromium E2E checks](https://github.com/parksy1625/cortex-debugger/actions/runs/39996800312),
[real GPT-2 on Apple Silicon MPS](https://github.com/parksy1625/cortex-debugger/actions/runs/39996476238),
[Python 77 tests + React build](https://github.com/parksy1625/cortex-debugger/actions/runs/39995932741).
See [M4 measured evidence](docs/M4_VALIDATION.md) for the CPU–MPS comparison.
Browser E2E against a **real** model server is not yet automated.

## Start locally

Requirements: Python 3.11+, Node.js 22+.

```bash
python -m pip install -e '.[dev,api,ml]'
pytest -q
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd apps/web
npm install
npm run dev
# Open http://127.0.0.1:5173
```

To run browser tests:
```bash
cd apps/web
npx playwright install chromium
npm run test:e2e
```

**Do not expose the API publicly.** It is unauthenticated and is intended to
bind to localhost only. First model execution downloads GPT-2 weights.

## Replay an experiment in CI

```bash
cortex validate experiments/regression/gpt2-dog-cat.json
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression.json \
  --junit artifacts/regression.xml
```

Exit statuses: 0 all checks pass, 1 regression assertion failure, 2 invalid
manifest or execution error. Supplying `--artifact` checks saved JSON **without
rerunning the model**. A manifest contains **raw prompts**; never commit private
or proprietary inputs.

Guides: [M4 studio](docs/M4_STUDIO.md) ·
[M3 replay](docs/M3_REGRESSION.md) ·
[Known limitations](docs/LIMITATIONS.md).

MIT license.
