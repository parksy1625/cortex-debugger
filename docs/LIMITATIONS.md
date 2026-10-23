# Known limitations — M5 v0.6-dev

- AI explanation remains **local intervention analysis**, not a complete
  model reasoning/circuit explanation.
- Model cache is process-local and deliberately holds a full GPT-2 bridge
  in memory. It trades RAM for less model loading and does not reduce
  per-experiment activation cache usage.
- A single Uvicorn worker is required. Running multiple processes will create
  independent caches and separate SQLite task queues. Never expose the API
  on a network; there is no authorization.
- No hard inference timeout, safe mid-run cancellation, or maximum process
  resident memory guard. Failed jobs do not retain private raw prompts in
  SQLite, but input token IDs are included in completed evidence.
- Live model browser tests use pinned GPT-2 and may download weights. The
  pipeline measures workflow correctness, not a representative benchmark.
- Python/Node package lock files are not yet complete. Exact GPT-2 revision is
  pinned, and TransformerLens 4.2.0 is pinned; Torch dependency varies by
  environment unless explicitly constrained in CI.
- Data exported as regression manifests contains raw prompts. Users must
  choose safe, nonprivate examples before committing them.
- Apple Silicon MPS was verified in M4 for one pinned experiment, not a
  cross-model numerical reproducibility guarantee.
- Remote multiuser security, signed provenance, cancellation deadlines and
  executable packaging are future work.
