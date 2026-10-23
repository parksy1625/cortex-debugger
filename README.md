# Cortex Debugger

**Local-first model intervention and debugging studio**

M2 (v0.3.0-dev) integrates the GPT-2 paired-prompt activation patching engine, a FastAPI single-worker job queue, SQLite experiment metadata, and a React dashboard for launching experiments and viewing measured activation RMS differences, logit margins and self-patch controls.

**Validation:** The real GPT-2 self-patch and paired-prompt smoke checks passed on GitHub Actions run [39992051722](https://github.com/parksy1625/cortex-debugger/actions/runs/39992051722). Model weights are now pinned to the Hugging Face commit SHA 607a30d783dfa663caf39e06633721c8d4cfcd7e. The code also has 43 local Python unit/integration tests. The web UI is implemented, but its Node dependency build has not yet been confirmed in this environment. The sample smoke experiment proves the intervention machinery operates, not that the default patch has a scientifically meaningful causal explanation.

## Quick start

Requirements: Python 3.11+, Node.js 22+. Run both terminals from the repository root unless otherwise noted.

```bash
python -m pip install -e '.[dev,api,ml]'
pytest -q
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd apps/web
npm install
npm run dev
# http://127.0.0.1:5173
```

The first experiment may download GPT-2 weights. The API has no user authentication and **must not be exposed to a network**. Model execution is serialized (one running and up to two waiting).

## M2 features

- Compare clean/corrupted prompts with a single residual activation patch.
- Record self-patch identity control, token×layer RMS activation deltas, and next-token logit margin recovery.
- Start an experiment through the browser; poll job states and cancel queued jobs.
- Browse recent experiment metadata and export JSON evidence.
- Store experiment results in SQLite at `~/.cortex-debugger/experiments.sqlite3` (override with `CORTEX_DATA_DIR`). Raw prompts are not persisted, but output token IDs can reveal prompt information.
- Run CLI `cortex pair`, `cortex smoke`, and `cortex score` unchanged from M1.

Full API and usage guide: [docs/M2_STUDIO.md](docs/M2_STUDIO.md). Scientific and technical limitations: [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Reproducibility and research caution

Activation differences are only descriptive. A single patch can demonstrate a localized intervention effect, not a model-wide explanation. Pin the model revision before attempting rigorous cross-run tests. Real-model validation and M3 regression assertion workflows remain outstanding.

## Project layout

- `apps/api/` — FastAPI + serialized worker + SQLite
- `apps/web/` — React + TypeScript experiment studio
- `packages/cortex-engine/` — TransformerLens bridge, patching, numeric metrics
- `tests/` — model-free and API integration tests
- `docs/` — experiment design and limitations
- `.github/workflows/` — CI and manual GPT-2 smoke validation

Licensed under MIT.
