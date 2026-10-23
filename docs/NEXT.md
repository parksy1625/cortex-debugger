# Next milestones

1. **M2 validation gate:** Run GitHub Actions Quality workflow (Python and web) and manual Model Smoke with GPT-2; inspect logs, rectify actual API/model compatibility problems, and attach measured evidence.
2. Pin verified GPT-2 Hugging Face model revision; record device, dtype, dependency versions, and seed in result metadata.
3. Add deterministic paired-prompt examples with aligned token positions and a numerical self-patch tolerance determined from measurements.
4. Add model session reuse, memory bounds, an inference timeout, queue recovery after process restart, and result retention policy.
5. **M3:** Build a versioned experiment assertion manifest, CLI replay, nonzero regression gate and JUnit report.
6. **M4:** Browser e2e tests, accessible heatmap keyboard controls, benchmarks, contribution docs and release workflow.
