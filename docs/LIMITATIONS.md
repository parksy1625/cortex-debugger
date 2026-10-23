# Known limitations (M1 engine, v0.2-dev)

- CLI paired-prompt intervention has unit tests against a synthetic bridge but has **not yet been run against real TransformerLens 4.2 + GPT-2 weights**.
- The React page is a system-status screen, not the interactive experiment GUI; API has no experiment job queue.
- GPU support is limited to experimental Apple MPS; CPU is the verification target.
- Model revision is selectable by 40-character SHA but not required: a null revision must be treated as unsuitable for regression verification.
- JSON artifacts contain input token IDs and derived statistics (potentially sensitive), not raw prompts/activation arrays.
- Only exactly one residual site is patched per experiment; token lengths must match and token positions may not be semantically aligned.
- Identity-control tolerance (1e-4) is a provisional engineering threshold that needs empirical calibration across systems/dtypes.
- No lockfiles, memory budgets, concurrent-job isolation, persistent experiment storage, or CI regression assertions yet.
- Do not expose the local API to the network; it has no authentication or rate limiting.
