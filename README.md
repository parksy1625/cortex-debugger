# Cortex Debugger

**Causal activation debugging for open-weight language models.**

> Stage **M0** — an initial, deliberately honest implementation scaffold. The complete MVP defined in [`docs/MVP_BLUEPRINT.md`](docs/MVP_BLUEPRINT.md) is **not yet built**.

Cortex aims to turn a paired-prompt activation-patching investigation into a reproducible regression test. Built on TransformerLens 4.x rather than reimplementing its instrumentation.

## Included today

- Pure Python, unit-tested `logit_margin` and unclamped `recovery_score` primitives.
- Explicit token-length and patch-coordinate validation.
- **Opt-in** GPT-2 self-patch smoke experiment via TransformerLens 4.x (download / run not verified in scaffold environment).
- Local FastAPI health and metrics endpoints, plus a React readiness dashboard.
- GitHub Actions unit checks and opt-in model smoke.

## Quick start

Requires Python 3.11+ (Node.js 22+ for UI).

```bash
python -m pip install -e '.[dev,api]'
pytest -q
python -m cortex_engine.cli info
cortex score --clean 2.0 --corrupted -1.0 --patched 1.0
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd apps/web
npm install
npm run dev
# http://127.0.0.1:5173
```

Model validation, separately (first run downloads GPT-2 and may need several GB of disk space):

```bash
python -m pip install -e '.[ml]'
cortex smoke --device cpu --layer 0 --token-index 0
```

Do not claim the self-patch test passed until it has actually been run. The [manual GitHub model-smoke workflow](.github/workflows/model-smoke.yml) makes this an explicit gate.

## Repository layout

- `packages/cortex-engine/src/cortex_engine`: local model analysis primitives and optional TransformerLens adapter
- `apps/api`: FastAPI local service
- `apps/web`: React dashboard (M0, no experiment GUI yet)
- `tests`: fast model-free tests
- `docs`: engineering plan, limitations, milestone tasks

## Project principles

1. A heatmap is descriptive; a controlled intervention supports localized causal claims.
2. Failing experiments and absent controls must be visible, never auto-accepted.
3. Run locally by default; never upload private prompts to a third party by default.
4. Pin the exact model revision before accepting cross-version regression tests.
5. Document what is tested and distinguish from what is planned.

MIT license. Contributions welcome after M0 model-hook validation.
