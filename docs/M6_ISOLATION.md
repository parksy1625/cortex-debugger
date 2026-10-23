# M6 — Isolated model worker and resource controls (v0.7-dev)

## Architecture

The web API keeps a bounded SQLite-backed job queue. Model execution takes
place in a separate Python **subprocess** launched with
`python -u -m apps.api.model_worker`. A single child retains the
previous pinned TransformerLens GPT-2 instance for repeated jobs;
the API parent never imports or allocates GPT-2 weights.

The child accepts only a fixed `pair` command over local JSON-lines stdin
and returns a JSON report over stdout. The parent discards child stderr,
sanitizes exceptions to class names, and persists derived reports, **not
raw prompts**, in SQLite. The parent may terminate the worker process
on running-job cancellation, wall-clock deadline, or RSS budget violation.
The next job starts a fresh subprocess. Any cancelled model cache is lost.

Job status transitions: queued → running → completed/failed;
queued/running → cancelled; running → failed on timeout/resource violation.

## Configuration

```bash
# Default: 180s deadline; 0 means no enforced memory budget.
export CORTEX_JOB_TIMEOUT_SECONDS=180
export CORTEX_WORKER_MEMORY_MB=0
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

The RSS budget is optional and uses psutil to sum model-worker and child
resident memory. Recommended configurable ceiling is higher than measured
GPT-2 peak use; setting a low value terminates model downloads/inference.
It is a **polling guard**, not an OS-enforced cgroup/rlimit hard memory limit:
short allocation spikes can exceed the budget between samples. GPU/MPS memory
allocations may not appear in process RSS. A hard OS memory cap remains
future work.

The timeout is enforced via subprocess termination, rather than sending
a cancellation flag to a running PyTorch thread. Parent should run one
Uvicorn process (`--workers 1`), not multiple API workers. No public
exposure, multi-tenant security or authentication exists.

## Verification

- Model-free subprocess tests verify warm reuse, revision key tracking,
  timeout and process restart, cancellation, budget violation, and
  SQLite persistence without raw prompt storage.
- CI runs a real-model API and Chromium E2E suite; this validates subprocess
  boundary and model reuse end-to-end (check actual GitHub Actions status).
- M3 pinned replay and M4 MPS smoke remain separate pipelines.

## Limits

- A kill can interrupt external model-cache writes; a later run may need to
  redownload or repair checkpoint cache files.
- No full process-tree hard kill guarantee for external detached processes.
- Default RSS guard disabled and not a strong sandbox; not a substitute
  for cgroups/job objects or operating system security boundaries.
- Large return payloads could consume parent memory; future versions should
  enforce an IPC message-byte limit before deserialization.
- Timeout applies to one experiment's model work, including a cold load.
- Model-process errors intentionally omit stack traces in client responses
  to avoid leaking raw prompts. Troubleshooting relies on local debugging.
- No release installer or fully reproducible dependency lockfile yet.
