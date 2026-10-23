# Known limitations (M0)

- No clean/corrupted pair GUI yet. The React view is a transparent readiness dashboard, not a completed debugger.
- The `smoke` command needs network access to download GPT-2 on first run (unless model is cached).
- Exact model weights SHA, dependency lockfiles, and reproducible builds are **not yet implemented**.
- A same-input self patch checks intervention machinery; it does **not** demonstrate causal recovery.
- Hook compatibility and `mps` numerical tolerance are not verified in this environment. The manual model smoke job is the first required validation.
- API exposes only health, model allowlist, and scalar metric endpoints, not an experiment job queue.
- Do not expose local API publicly before adding auth, CORS policy, rate limits, file limits, and other safeguards.
