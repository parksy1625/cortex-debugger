# Contributing

Current stage: M0 technical proof. Please start with an issue explaining the proposed change and an objective test.

```bash
python -m pip install -e '.[dev]'
ruff check packages/cortex-engine/src apps/api tests
pytest -q
```

Do not upload proprietary prompts, model checkpoints, tokens, or personal data. Reproduction artifacts must identify model revision, device, dtype, and measured tolerance. Never claim heatmap differences alone prove causation.
