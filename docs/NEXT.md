# M4 follow-up

1. Confirm Browser E2E GitHub workflow passes Chromium route-mocked tests.
2. Add Apple Silicon MPS measurement and CPU/MPS comparison via real Mac hardware.
3. Add complete end-to-end browser + real GPT-2 integration test (opt-in due to model cost).
4. Make model worker reuse cached weights, enforce execution deadlines and safe cancellation.
5. Add reproducible Python/JS lock files and capture environment / dtype / tokenizer in experiment reports.
6. Add privacy-safe manifest templating (no raw prompts in public repos) and signed evidence provenance.
7. Extend adapters to additional model families only after architecture-specific hook validation.
