# M7 — Privacy and measured reproducibility

## User-visible additions

### Shareable JSON

The **Export redacted summary** action calls
`GET /api/v1/experiments/{id}/shareable`. This endpoint constructs a new
allowlisted report from completed and successful experiments only.
It intentionally omits **prompt text, all token IDs, candidate token IDs,
SHA-256 prompt fingerprints, experiment ID, original errors, filesystem paths,
raw cache arrays and full runtime metadata**.

The output retains model identity/revision, device, patch location and
aggregate margin/recovery/identity-control measurements. **Aggregate scores
may still be sensitive** when combined with outside information. The report
cannot be replayed and is explicitly marked redacted.

### Delete local experiment

`DELETE /api/v1/experiments/{id}` returns HTTP 204 for terminal jobs. A
running/queued job returns HTTP 409; cancel it first. Records vanish from
SQLite's logical table and the History UI. This is **not cryptographic
erasure**: SQLite WAL pages, snapshots, backup copies and disk remnants
may retain previous bytes. Full erasure requires lifecycle management beyond
a DELETE statement.

The browser presents a confirmation dialog with this caveat. No scheduled
retention defaults or automatic deleting of other users' data.

## Benchmark

For a *measured* cold/warm series on Linux CPU or Apple Silicon MPS:

```bash
python -m pip install -e '.[ml,api]'
python -m scripts.benchmark_model --runs 3 --device cpu \
  --output artifacts/m7-benchmark.json
```

The benchmark exercises a pinned GPT-2 experiment through the same subprocess
boundary used by the API. It records cold and warm wall-clock durations,
whether the child reused a cached model, model boot time, forward-pass duration,
single-run recovery, and **sampled** peak process RSS. The CPU CI workflow
uploads a JSON artifact; read the artifact before asserting any speedup.

- A cold run includes model load and may include downloading weights.
- Warm runs reuse the model already held by the process.
- `observed_cold_to_warm_ratio` is one hardware-run observation, **not**
  general throughput or model-compute speedup.
- RSS peaks are sampled (50ms polling), not enforced kernel peaks, and
  do not fully account for MPS unified memory.
- Preserve hardware architecture, torch versions, input tokens, model revision
  and runner configuration when making comparisons.

## Installation and lockfiles

Versioned install scripts and dependency manifests are tracked separately.
The Python model revision is pinned, but transitive Python and Node
dependencies have not yet all been committed as platform-specific lockfiles.
Do not claim bit-for-bit reproducibility until their lockfiles and
`npm ci`/locked install paths pass on CI.

## Safety and status

The API remains intended for localhost. No authorization, internet-facing
deployment, or secure multi-user tenancy. Do not publish raw M2/M3 evidence
and regression manifest files containing prompts.
