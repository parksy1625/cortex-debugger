# Current limitations — M2 v0.3-dev

- **No real TransformerLens/GPT-2 run verified yet.** The paired-prompt engine has synthetic torch tests and the FastAPI integration has fake-model worker tests, which cannot prove real hook compatibility.
- **Front-end build pending.** React TSX syntax verified in isolation; package install, type check, production build, and browser e2e checks need a connected Node environment/GitHub CI.
- Only GPT-2, max 128 tokens, same sequence length, single-token answer candidates, and one layer/token residual patch.
- MPS support unvalidated. The identity-control tolerance needs measured device/dtype calibration.
- Local API deliberately unauthenticated; bind to `127.0.0.1` only. No remote deployment, user accounts, or cross-origin sharing.
- Models are loaded per job; cold start may be slow. No hard inference deadline or safe mid-inference cancellation.
- The job queue is process-local, max 1 running + 2 queued. Restart doesn't resume pending jobs.
- SQLite results omit raw prompts but contain token IDs, hashes, and output measurements; users must protect those files.
- Not yet suitable for regression gates: model revision can be omitted, no deterministic model baseline manifests or CI assertions.
- RMS heatmaps visualize difference, not causation. Patching effects are limited to these inputs and this model.
