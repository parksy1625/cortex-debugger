# M3 validation report — 2026-10-24 (Asia/Seoul)

## GitHub Actions evidence

- [Pinned model regression run #39994357934](https://github.com/parksy1625/cortex-debugger/actions/runs/39994357934) — **success**, source commit `3f6da0a168764d70b78bc3c8c28f9814cd214799`.
- Real GPT-2 weights were loaded on GitHub-hosted Linux CPU runners, using the exact model revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`.
- `cortex validate experiments/regression/gpt2-dog-cat.json` — **success**.
- `cortex verify ... --report ... --junit ...` — **success**.
- Verification report: **13 checks passed, 0 failed**, mode **replay** (“Pinned model was rerun”), not `--artifact`.
- CI artifact: `cortex-gpt2-regression` (GitHub Actions artifact ID **12518304037**), containing `regression-report.json` and JUnit XML; hosted by GitHub's artifact retention policy.
- [Python+web quality check #39994490378](https://github.com/parksy1625/cortex-debugger/actions/runs/39994490378) — **success** on follow-up lint-fix commit `893ce493`; **76 Python tests passed**, Ruff clean, React TypeScript production build successful, CLI manifest validation successful.

## What this proves

A versioned JSON regression manifest is parseable and strictly validated. The CLI can load the pinned model, perform a fresh paired-prompt intervention, verify model/prompt/patch identity, apply numerical bounds and emit the expected CI exit status/JUnit report. Unit tests also exercise intentionally mismatched metadata, forbidden model revisions, malformed manifests, out-of-range metrics, undefined recovery and exit statuses 0/1/2.

## What this does *not* prove

- A verified causal explanation of GPT-2. The dog/cat experiment is a minimal mechanical example, not a validated mechanistic circuit.
- Robust behavior across other models, prompts, devices, library versions, seeds, or dtypes.
- Tamper-proof authenticity of offline JSON artifacts, which are untrusted input.
- Browser end-to-end or Apple MPS integration.
- That GitHub branch protection is configured. To make failed checks merge-blocking, enable required checks in the repository rules/settings.

The successful real-model run was triggered from commit `3f6da0a`. Later commits only fix the Python test suite's imports; the model and regression engine code was unchanged. The latest quality check validated those changes independently.
