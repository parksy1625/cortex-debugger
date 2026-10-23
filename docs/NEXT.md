# Development roadmap (after M1 engine)

1. **M1 validation**: run manual GPT-2 self-patch and paired-prompt workflow (TransformerLens 4.2.0), pin weights revision, record timings/numerical parity.
2. **M1 refinement**: test meaningful aligned clean/corrupted prompt pairs, per-layer activation deltas, and actual intervention scores.
3. **M2 UI**: bounded single-worker FastAPI job queue, per-experiment SQLite metadata, React prompt editor, layer×token RMS heatmap and patch inspector.
4. **M3 regression**: schema-versioned assertion configuration, strict model-revision matching, verified replay and nonzero CI failures on assertion violations.
5. **M4 open source**: reproducible benchmarks, examples, documentation of limits, release workflow and model-weight safety checks.
