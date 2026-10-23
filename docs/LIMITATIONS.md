# Current limitations — M2 v0.3-dev

- **Real CPU TransformerLens/GPT-2 model smoke verified** in run 39992051722 after correcting the hook callback signature; one example does not validate all interventions or scientific attribution.
- **Front-end production build verified** in GitHub Actions; browser e2e and real model-run UI walkthrough remain pending.
- Only GPT-2, max 128 tokens, same sequence length, single-token answer candidates, and one layer/token residual patch.
- MPS support unvalidated. The identity-control tolerance needs measured device/dtype calibration.
- Local API deliberately unauthenticated; bind to `127.0.0.1` only. No remote deployment, user accounts, or cross-origin sharing.
- Models are loaded per job; cold start may be slow. No hard inference deadline or safe mid-inference cancellation.
- The job queue is process-local, max 1 running + 2 queued. Restart doesn't resume pending jobs.
- SQLite results omit raw prompts but contain token IDs, hashes, and output measurements; users must protect those files.
- Default model weights are pinned to an exact revision, but strict regression replay and CI assertions remain unimplemented.
- RMS heatmaps visualize difference, not causation. Patching effects are limited to these inputs and this model.
