# Roadmap after M5

1. Review real browser→API→GPT-2 and repeat-model tests and confirm cache
   measurements; resolve any workflow failures without masking them.
2. Document cold/warm end-to-end latency with repeatable CPU/MPS runs.
3. Move model execution into a worker process for enforceable deadlines,
   cancellation and memory isolation (threads cannot safely kill PyTorch).
4. Add secure local artifact retention/deletion policy and redact token IDs
   from optional shared reports.
5. Add complete platform-specific `uv.lock` and Node package-lock, verified
   with reproducible GitHub Actions installations.
6. Add desktop packaging and user onboarding; never deploy unauthenticated
   inference API publicly.
7. Research multi-model adapters only after preserving token and hook semantics.
