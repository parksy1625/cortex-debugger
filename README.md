# Cortex Debugger

**Local-first AI model debugger and pinned GPT-2 regression workbench.**

M7 (v0.8.0-dev) adds practical privacy management and repeatable performance
measurement to M6 subprocess isolation, M5 caching, and the M3 regression gate.

## Features

- Clean/corrupted prompt activation patching with layer/token heatmap.
- Pinned GPT-2 real-model replay with strict numeric assertions and JUnit CI.
- Local React studio, FastAPI/SQLite history, bounded queue, live cancellation,
  180s default deadline and optional sampled RSS budget.
- **M7: Shareable redacted summaries** exclude raw prompts, token IDs,
  prompt hashes, experiment IDs and file paths.
- **M7: Delete terminal experiment records** through History with confirmation.
  This is logical SQLite deletion, **not secure wiping of snapshots/WAL/backups**.
- **M7: measured cold/warm benchmark** (subprocess wall clock, cache-hit,
  model-load time and sampled worker RSS) with GitHub Actions artifact.

## Run locally

Requires Python 3.11+, Node.js 22+:

```bash
python -m pip install -e '.[ml,api,dev]' -c requirements-linux-py311.lock
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm ci
npm run dev
# http://127.0.0.1:5173
```

For deterministic model-replay assertions:

```bash
cortex validate experiments/regression/gpt2-dog-cat.json
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression.json --junit artifacts/regression.xml
```

For cold/warm performance (real model weights will download on first use):

```bash
python -m scripts.benchmark_model --runs 3 --device cpu
```

The benchmark ratio is **one measured example**, not a general acceleration
claim. Mac MPS results require running on genuine Apple hardware.

## Privacy and security

This is a localhost-only unauthenticated research tool. **Do not expose it to
the network.** Shareable summaries still contain aggregate scores; review
before sharing. JSON regression manifests contain **raw prompts**. Full
experiment evidence may contain token IDs that reveal prompt information.

Measured and locked CI results: [M7 validation](docs/M7_VALIDATION.md). Linux Python dependency versions are constrained through [requirements-linux-py311.lock](requirements-linux-py311.lock), and the web app uses [package-lock.json](apps/web/package-lock.json) with `npm ci`. The Linux constraints are **not a cross-platform, hash-verified environment lock**; on Apple Silicon, install according to the platform instead of applying the Linux file.

Docs: [M7 privacy and benchmark](docs/M7_PRIVACY_BENCHMARK.md) ·
[M6 worker safety](docs/M6_ISOLATION.md) ·
[M5 real-model validation](docs/M5_VALIDATION.md) ·
[M4 Apple MPS](docs/M4_VALIDATION.md).

MIT License.
