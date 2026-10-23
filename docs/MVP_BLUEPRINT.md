# Cortex Debugger — MVP Engineering Blueprint

Date: 2026-10-24 | Status: M0 scaffold, not a completed model debugger.

## Goal

Build a local-first mechanistic-interpretability developer tool that converts clean/corrupted prompt activation-patching experiments into reproducible CLI/CI regression tests.

The differentiator is a product-workflow hypothesis, not a novel patching algorithm. TransformerLens, NNsight, Neuronpedia, mechinterp-probe and TransInterp already cover significant pieces of the technical workflow.

## M0 implemented

- GPT-2 allowlist, optional TransformerLens 4.x self-patch adapter.
- Pure numeric margin/recovery primitives and input coordinate validation.
- Local FastAPI health and metrics endpoints, CLI, React readiness screen.
- Python unit tests and GitHub Actions quality workflow.
- No real paired-prompt visual debugger, experiment storage, regression runner or validated model smoke yet.

## Proposed M1–M4 scope

1. Resolve and pin exact GPT-2 Hugging Face commit SHA; verify TransformerBridge hooks on CPU and Apple MPS.
2. Accept paired clean/corrupted prompts, equal tokenized lengths (<=128 tokens) and candidate single-token answers.
3. Cache selected residual activations at blocks.{layer}.hook_out. A heatmap of scaled residual deltas is descriptive, not causal.
4. Patch one clean activation vector into corrupted run and measure next-token candidate logit margin. Require self-patch control.
5. Persist schema-versioned JSON evidence with revision, tokenizer IDs, dtype/device, seed, parameters, metrics, and numerical tolerances; raw prompts and activations only with opt-in.
6. Implement CLI verification with explicit assertions and nonzero exit on failures; distinguish assertion failures from environment/model revision errors.
7. Implement FastAPI single-worker bounded job queue, SQLite experiment metadata, React paired-prompt editor/heatmap/patch inspector.
8. Expand GitHub Actions with reproducible CPU integration tests and documented MPS differences.

## Metric definitions

Next token: S(x) = logit(correct token) - logit(incorrect token)

Normalized recovery: R = (S(patched) - S(corrupted)) / (S(clean) - S(corrupted))

Return undefined when denominator is sufficiently near zero; never clamp the ratio. A positive change from one intervention is evidence limited to that model, prompt, component, and method.

## Intended architecture

React TypeScript / Vite → localhost FastAPI → single experiment worker → independent Python cortex-engine → TransformerLens 4.x → PyTorch CPU/MPS; with SQLite metadata and versioned JSON export. No cloud uploading by default.

## Future API

- GET /api/v1/health and /api/v1/models (M0)
- POST /api/v1/experiments (M1+)
- GET /api/v1/jobs/{id} (M1+)
- GET /api/v1/experiments/{id} (M1+)
- POST /api/v1/experiments/{id}/patch (M2+)
- POST /api/v1/experiments/{id}/assertions (M3+)
- GET /api/v1/experiments/{id}/bundle (M3+)

## Planned CLI

- cortex run experiments/ioi-example.yaml --out artifacts/ioi/
- cortex inspect artifacts/ioi/
- cortex verify experiments/ioi-example.yaml --device cpu --output junit.xml

Only 'cortex info', 'cortex score' and 'cortex smoke' exist in M0. The YAML sample is intentionally marked as not executable yet.

## Scope, privacy and truthfulness

No arbitrary user-supplied model code, unpinned model revisions, large-model distributed inference, false causal claims from heatmaps, automatic baseline acceptance, or public binding of the local API. Validate request sizes and model allowlists. Limit workers and memory. Publish measured performance only after reproducible testing.

## Acceptance gates

- CPU GPT-2 self-patch runs successfully with an experimentally justified tolerance.
- Exact model revision is pinned and recorded.
- The same input self-patch produces near-identical logits.
- Paired-prompt experiment and intervention run end-to-end.
- CI verification rejects a deliberately violated assertion.
- README clearly separates delivered features and planned features.

## Relevant prior art

- https://github.com/TransformerLensOrg/TransformerLens
- https://nnsight.net/
- https://docs.neuronpedia.org/
- https://github.com/DipinDevSaji/mechinterp-probe
- https://github.com/Zoe4370/TransInterp

This blueprint is a compact repository adaptation of the full project specification; no M1–M4 features are asserted to be implemented yet.
