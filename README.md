# Cortex Debugger

**AI model activation debugger and reproducible regression workbench.**

M6 / v0.7.0-dev adds **isolated GPT-2 execution** to the validated
M5 model cache, React experiment studio and pinned-model regression runner.

## Capabilities

- Compare a clean vs corrupted prompt and patch one residual activation.
- Visualize layer×token differences, logit margins and self-patch control.
- Create validated, versioned regression JSON from the browser (contains
  raw prompts; keep private inputs out of public repositories).
- Re-run the pinned model with `cortex verify`, emit JUnit and fail CI
  on out-of-bound changes.
- **M6: one persistent model subprocess, one running job + two queued**.
  Running model work can be cancelled by killing its isolated worker.
- **M6: enforce per-job deadline** (default 180s) and optional sampled
  process RSS memory budget. A new task restarts a killed worker.
- SQLite stores derived model evidence and status without saving raw prompts.

## Local development

Python 3.11+, Node 22+:

```bash
python -m pip install -e '.[dev,api,ml]'
pytest -q
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm install
npm run dev
# Open http://127.0.0.1:5173
```

Set `CORTEX_JOB_TIMEOUT_SECONDS=180` and optionally
`CORTEX_WORKER_MEMORY_MB=0`. A value of 0 disables the RSS guard.
Use exactly **one** API server process: each additional worker has its
own queue and model subprocess. This is a localhost-only unauthenticated
research tool; **do not expose it on the network**.

## Regression CI

```bash
cortex validate experiments/regression/gpt2-dog-cat.json
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression.json --junit artifacts/regression.xml
```

`--artifact` is an **offline** check: it does not rerun GPT-2.
**M6 CI validation succeeded:** [86 Python tests + React build](https://github.com/parksy1625/cortex-debugger/actions/runs/40002751276),
[real GPT-2 API + browser E2E](https://github.com/parksy1625/cortex-debugger/actions/runs/40002751327).
See the [full M6 verification report](docs/M6_VALIDATION.md).

See [M6 isolation and resource limits](docs/M6_ISOLATION.md),
[M5 real-model validation](docs/M5_VALIDATION.md),
[M4 CPU/MPS measurements](docs/M4_VALIDATION.md) and
[known limitations](docs/LIMITATIONS.md).

CI must run on each change. Actual throughput and memory savings must be
measured before making quantitative performance claims.
