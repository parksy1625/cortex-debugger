# After M10

1. Complete: M10 published independently as v0.10.0-rc1, validated by
   actual GPT-2 browser/package smoke on Linux and native launchers on
   Apple Silicon MPS and Windows x64.
2. Complete: browser Host/Origin/Fetch-Site safeguards, model-free runtime
   diagnostics and 1 MiB model-worker IPC response budget.
3. Highest priority: **actual local API authentication or owner-bound IPC**;
   Host/Origin checks are not sufficient against malicious local programs.
4. Implement detailed first-run install/model download progress and correct
   error recovery in desktop launchers, plus real GUI click automation.
5. Add signed/notarized macOS/Windows releases with trusted publisher
   credentials managed outside source control. Document update/rollback.
6. Implement OS hard memory limits where possible, controlled data retention,
   and safe user-selectable local-model and checkpoint storage.
7. Expand causal experiment breadth only after model validation and
   reproducibility test coverage.
