# M6 verification — 2026-10-24 KST

## Completed GitHub Actions

| Verification | Result | Source |
| --- | --- | --- |
| Python/Ruff and React production build | **PASS**: 86 passed, 1 opt-in real-model test skipped | [run 40002751276](https://github.com/parksy1625/cortex-debugger/actions/runs/40002751276) |
| Real GPT-2 API and live Chromium E2E | **PASS**: 1 real HTTP/cache test + 1 real browser test | [run 40002751327](https://github.com/parksy1625/cortex-debugger/actions/runs/40002751327) |
| Existing pinned GPT-2 regression replay | **PASS** on preceding M6 engine commit | [run 40002621508](https://github.com/parksy1625/cortex-debugger/actions/runs/40002621508) |
| Mocked Chromium workflow | **PASS** on preceding M6 engine commit | [run 40002621612](https://github.com/parksy1625/cortex-debugger/actions/runs/40002621612) |

The latest validated implementation commit was `6e07a48f`; the initial M6 implementation `9166a01d` surfaced a real cancellation race which was repaired. The later cancellation-only correction does not alter the GPT-2 patch mathematics.

## New isolation test evidence

Five additional model-free subprocess tests cover:
1. Reusing a persistent subprocess and restarting it after shutdown.
2. Enforcing a short deadline, killing the subprocess, then executing a new job.
3. Cancelling a running child without incorrectly reporting worker crash.
4. Sampling and enforcing a deliberately small RSS budget.
5. Cancelling a running SQLite-backed experiment and completing another job after process restart.

The browser UI now offers **Cancel experiment** during queued and running states, and the API returns cancellation status for isolated running jobs.

## Architecture and security limits

- The GPT-2 worker process communicates by newline-delimited JSON over
  standard input/output. Child stderr is discarded and errors are sanitized
  to a class name to avoid echoing private prompts.
- **Default timeout:** 180 seconds; configurable using
  `CORTEX_JOB_TIMEOUT_SECONDS`.
- **Optional RSS budget:** `CORTEX_WORKER_MEMORY_MB=0` is **disabled** by
  default. When nonzero, psutil polls process RSS and terminates the worker
  if its observed footprint exceeds the set threshold.
- Process memory polling is **not** the same as a cgroup, rlimit or kernel
  memory hard cap. It may miss transient spikes and GPU allocations.
- One API process with one worker only. Multiple Uvicorn workers and network
  exposure are unsupported.
- Killing the subprocess loses the in-memory model cache and triggers a new
  weight load on the next job. Model downloads interrupted mid-write may
  require cleanup or re-download.
- Model evidence can contain token IDs and downloaded regression manifests
  contain the source prompts. Treat both as potentially sensitive.
- Full lockfiles, signed provenance, multi-user security and platform-specific
  hard memory isolation remain outstanding.

## Interpretation

This M6 release is a developer prototype with **actual process-backed model
execution and cancellation** and GitHub CI that validated the real GPT-2
API/browser path. It is not yet a hardened publicly hosted inference service.
