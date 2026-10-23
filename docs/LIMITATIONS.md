# Known limitations (M4 v0.5-dev)

- Real GPT-2 model replay and numerical regression passed 13/13 checks in GitHub Actions #39994357934, a limited mechanical example rather than a causal explanation of all model behavior.
- Browser e2e uses mocked API (not real GPT-2); review [.github/workflows/browser-e2e.yml](../.github/workflows/browser-e2e.yml) for latest status.
- Creating regression JSON in browser requires raw prompt texts, which are held only in browser memory and written to the downloaded JSON. NEVER publish manifests with confidential prompts.
- SQLite does not save raw prompts, but token IDs and derived values can reveal information.
- Only GPT-2 is supported, <=128 tokens, matching lengths, single-token candidates and one patched residual per experiment.
- API is intentionally unauthenticated; 127.0.0.1 only. Do not expose on a public port.
- Queue: 1 running, 2 waiting; startup now marks orphaned previous jobs failed. No hard timeout, live inference cancellation, or model reuse guarantee.
- Actual Apple Silicon MPS and end-to-end browser execution against real weights are not yet measured.
- Browser export generates sample engineering tolerances, not scientifically justified confidence bounds.
- Exact environment pinning, signed provenance, model revision comparison and remote multiuser security are future work.
