# Known limitations — M7 v0.8-dev

- Redacted reports are allowlist-based and exclude prompts, token IDs,
  hashes, experiment IDs and file paths; aggregate metrics may still be sensitive.
- Deleting an experiment is a logical SQLite DELETE, not secure data erasure
  from SQLite WAL pages, filesystem snapshots or backups.
- Default model worker timeout 180s. Optional RSS budget uses psutil polling,
  not cgroups, VRAM accounting, or an OS-enforced hard memory cap.
- Process/worker model cache holds GPT-2 in memory between experiments.
- CPU cold/warm benchmarks contain substantial startup variance;
  they are measurements on one CI runner, not cross-platform speed guarantees.
- Python transitive and Node full lockfiles are not yet independently
  verified and committed. Do not claim fully reproducible installs.
- GPT-2 has a pinned weight revision but is not a general causal explanation.
- API has no authentication or public-network security; use localhost only.
- One Uvicorn process. Multi-worker process-local job queues unsupported.
- Signed artifact provenance and installer packages not finished.
