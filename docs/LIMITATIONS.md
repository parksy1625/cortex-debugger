# Current limitations — M3 v0.4-dev

- Real GPT-2 CPU self-patch and paired patch were verified in GitHub Actions run 39992734283, pinned model revision 607a30d783dfa663caf39e06633721c8d4cfcd7e.
- M3 adds strict replay and CI assertions, but the baseline is a **single simple token test**, not a scientifically established mechanism.
- Pinned M3 model replay passed **13/13** checks on GitHub Actions run 39994357934; later test-only lint fixes passed quality checks on run 39994490378. See [validation report](M3_VALIDATION.md).
- The model manifest includes raw non-sensitive example prompts; **do not commit private inputs**.
- "cortex verify --artifact" checks JSON contents without model execution or signed provenance. It must not be presented as fresh inference.
- Version/dtype/seed metadata are not yet comprehensive. CPU model revision pinned; Apple MPS remains unvalidated.
- M2 GUI experiments are not yet connected to regression authoring; M3 is accessible through CLI and CI.
- Local API has no authentication; **bind only to 127.0.0.1**.
- Model loads per job; bounded queue 1 running + 2 waiting. No inference timeout or safe cancellation mid-run; restart does not resume jobs.
- SQLite results omit raw prompts but contain token IDs, hashes, and output measurements, which are sensitive.
- RMS visualizations are descriptive rather than causal. Patching proves only the measured localized intervention outcome.
