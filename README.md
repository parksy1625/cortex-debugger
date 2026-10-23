# Cortex Debugger

**Causal activation debugging for open-weight language models.**

> Version **0.2.0-dev (M1 engine)** — local paired-prompt activation patching is implemented in the CLI; the interactive GUI and automated regression runner are planned. Model-backed TransformerLens execution has not yet been validated.

Cortex Debugger aims to turn model interventions into reproducible AI regression tests. This product workflow—not activation patching itself—is the proposed differentiator over existing interpretability tools.

## Current capabilities

- `cortex pair`: GPT-2 clean/corrupted prompt comparison with bounded token length, one residual patch, identity control, logit margin recovery, per-layer RMS differences and JSON report.
- `cortex smoke`: optional GPT-2 same-input self-patching to check hook compatibility.
- `cortex score`: deterministic normalized logit-margin recovery calculator.
- Local FastAPI endpoints (`/api/v1/health`, `/models`, and numeric metrics).
- React readiness dashboard. **Does not yet show actual activation heatmaps.**
- Python unit tests, GitHub Actions checks, and an **opt-in** real-model smoke workflow.

## Quick start

Python 3.11+ (Node.js 22+ for web):

```bash
python -m pip install -e '.[dev,api]'
pytest -q
cortex info
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm install
npm run dev
```

### Run a real GPT-2 experiment (downloads model weights)

```bash
python -m pip install -e '.[ml]'
cortex smoke --device cpu --layer 0 --token-index 0
cortex pair --clean 'The dog runs' --corrupted 'The cat runs' \
  --correct-token ' dog' --incorrect-token ' cat' \
  --layer 5 --token-index 1 --device cpu --output artifacts/example.json
```

A paired prompt must yield identical GPT-2 tokenized lengths. Candidates must each be exactly one token. Use `--revision` with the full Hugging Face model SHA for reproducible experiments. The example is a mechanical demo, not a validated circuit finding.

## Source and project plans

- Engine: [`packages/cortex-engine`](packages/cortex-engine/src/cortex_engine)
- CLI: [`cortex_engine/cli.py`](packages/cortex-engine/src/cortex_engine/cli.py)
- API: [`apps/api`](apps/api)
- Web: [`apps/web`](apps/web)
- M1 user guide: [`docs/M1_ENGINE.md`](docs/M1_ENGINE.md)
- Roadmap: [`docs/NEXT.md`](docs/NEXT.md) and [`docs/MVP_BLUEPRINT.md`](docs/MVP_BLUEPRINT.md)
- Limitations: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md)

## Research integrity and privacy

Activation differences alone do not prove causation. A single intervention's effect is local to a model, prompt, and method. Prompts are hashed rather than saved to the JSON report; output token IDs can still expose sensitive information. No automatic third-party telemetry or cloud upload by default. Do not expose the local API to untrusted networks.

MIT License · Open-source contributions are welcome.
