# M1 development tickets

1. Pin GPT-2 revision SHA and dependency resolution; record environment and hook availability.
2. Measure CPU GPT-2 self-patch precision; run `model-smoke` workflow and record outcome.
3. Add same-token-length clean/corrupted pair cache and residual-stream delta summary.
4. Add guarded candidate single-token ID validation, score recovery, and repeatable interventions.
5. Add JSON manifest (schema version + revision + token IDs + device/dtype + scores) and assertion runner.
6. Add FastAPI single-worker job queue, experiment persistence, and experiment API.
7. Add React prompt editor, selectable layer/token heatmap, patch inspector, and result report.
8. Add CPU regression suite and GitHub CI assertion gate.
