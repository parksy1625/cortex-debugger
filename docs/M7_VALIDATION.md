# M7 validation report — 2026-10-24 (Asia/Seoul)

## CI evidence

- [Linux Python/Ruff and React production build — PASS](https://github.com/parksy1625/cortex-debugger/actions/runs/40008656543). Previous source-only quality run [#40007693918](https://github.com/parksy1625/cortex-debugger/actions/runs/40007693918) passed **93 Python tests** with one optional real-model test skipped.
- [Chromium browser E2E — PASS](https://github.com/parksy1625/cortex-debugger/actions/runs/40008656539). Five mocked API browser tests passed; the separate live-model browser test is intentionally skipped by default.
- [Live FastAPI → actual GPT-2 model → React/Chromium — PASS](https://github.com/parksy1625/cortex-debugger/actions/runs/40008656787).
- [Pinned GPT-2 replay regression — PASS](https://github.com/parksy1625/cortex-debugger/actions/runs/40008656584).
- [Dependency lock generation — PASS](https://github.com/parksy1625/cortex-debugger/actions/runs/40008454566). Committed `apps/web/package-lock.json` and `requirements-linux-py311.lock` with `torch==2.7.1`. CI uses `npm ci` and Linux pinned Python constraints.

## Actual cold/warm benchmarks — pinned GPT-2 CPU

Same public example, model revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`, 3 consecutive
model-intervention experiments on separate GitHub-hosted Linux x86-64
runners. Runs include initial model loading and use the same subprocess
across all three attempts.

| Metric | Initial run #40007597869 | Locked environment run #40008656542 |
| --- | ---: | ---: |
| Cold wall clock | 18.9419 s | 8.6039 s |
| Warm run 1 | 0.2984 s | 0.3322 s |
| Warm run 2 | 0.2986 s | 0.3276 s |
| Warm median | 0.2985 s | 0.3299 s |
| Cold / warm observed ratio | 63.457× | 26.080× |
| Sampled peak model-worker RSS | 1031.79 MB | 1024.50 MB |

The **vast difference in cold latency across two runners demonstrates why
one-time startup ratios must not be advertised as stable speedups**.
The controlled result here is that a warm run did **not boot the model again**.
It does not mean transformer forward passes run 26–63 times faster.
The RSS peak is periodically sampled and excludes unaccounted GPU allocations
and transient peaks.

- [Benchmark #40007597869](https://github.com/parksy1625/cortex-debugger/actions/runs/40007597869) / [JSON artifact](https://github.com/parksy1625/cortex-debugger/actions/runs/40007597869/artifacts/12524244612).
- [Constrained benchmark #40008656542](https://github.com/parksy1625/cortex-debugger/actions/runs/40008656542).

## Privacy tests and behavior

- Completed experiment records can return a strictly allowlisted, locally
  downloadable JSON summary without token IDs, prompt hashes, experiment IDs,
  raw prompts or file paths.
- Only terminal experiment rows can be logically deleted from SQLite.
  Pending/running jobs get HTTP 409 and must be cancelled/finished.
- API tests cover redaction, invalid scores, incomplete runs, terminal-only
  deletion, 404 behavior and DB row removal; browser tests cover confirmation
  and cancellation of deletion.
- **A SQLite DELETE is not secure erasure.** Backups, journal/WAL remnants,
  system snapshots and copied reports need separate handling. Metrics
  retained in shared summaries may still contain sensitive inferences.

## Reproducibility status

- Model checkpoint pinned by exact Hugging Face SHA.
- Linux Python 3.11 dependency versions recorded in requirements lock,
  constrained to Torch 2.7.1; Node v22 packages in npm lockfile.
- `pip install -e ... -c requirements-linux-py311.lock` and `npm ci`
  were verified through GitHub Actions.
- Not yet hash-pinned wheel bytes across architectures; no guarantee of a
  bit-for-bit identical Mac MPS or Windows setup.
- API remains localhost-only without authorization; do not publish it.
