# Known limitations — M6 (v0.7-dev)

- The worker process separates PyTorch state from the API process and allows
  forcible cancellation, but this is **not an adversarial security sandbox**.
- The per-experiment timeout is hard at the subprocess lifetime level;
  RSS memory budget uses periodic psutil sampling and can miss transient peaks.
  Device VRAM and Apple unified-memory allocator accounting need further
  verification.
- Multiple Uvicorn processes are **unsupported** with process-local task
  queues and model worker. Bind only to localhost; no authentication.
- Model loading can be interrupted, potentially requiring checkpoint cache
  cleanup or redownload.
- Enforced cap on IPC output length and rate limiting are not yet implemented.
- Completed JSON artifacts include prompt token IDs; manifest downloads
  contain full raw prompts. Do not publish private data.
- Only one model family (pinned GPT-2), one activation site at a time,
  bounded token lengths and candidate IDs are currently supported.
- No platform-specific complete dependency lockfiles, reproducible package
  installer, signed artifacts, or diverse benchmark distribution.
- M5 real model E2E proves end-to-end work with thread worker; M6
  subprocess E2E must be checked in the new GitHub Actions run.
