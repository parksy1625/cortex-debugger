# Measured GPT-2 model-backed results (M2)

**Evidence:** [GitHub Actions run 39992734283](https://github.com/parksy1625/cortex-debugger/actions/runs/39992734283) · [experiment artifact](https://github.com/parksy1625/cortex-debugger/actions/runs/39992734283#artifacts) · source commit [a2f27d7](https://github.com/parksy1625/cortex-debugger/commit/a2f27d7c5cabd99a1e5bdd15fd2a4fad06baff14)

**Date:** 2026-10-24 KST (GitHub UTC logs: 2026-10-23 17:11)

## Reproducibility context

- Model: `openai-community/gpt2`
- Exact Hugging Face revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- Execution: GitHub Actions Ubuntu Linux CPU, Python 3.11, `transformer-lens==4.2.0`
- The CI workflow installed the model and recorded machine output. GPU/MPS verification is still outstanding.
- Self-patch experiment: layer 0, token index 0, max absolute logit delta **0.0** (declared tolerance 0.0001), outcome **pass**.
- Paired-prompt experiment: clean `The dog runs`, corrupted `The cat runs`, candidate next tokens ` dog` / ` cat`, patch layer 5, token index **2**.
- Token count per prompt: 4; the differing dog/cat token is at position 2 (including GPT-2's prepended special token).
- Logit margins: clean **0.8115386963**, corrupted **-0.3125610352**, patched **0.8504791260**.
- Normalized recovery: **1.0346414367** (about **103.46%**). Ratios above 100% are possible; the value is deliberately not clamped.
- Identity control within paired experiment: max absolute logit delta **0.0**, outcome **pass**.

## Interpretation and boundaries

This measurement establishes that the implementation can capture and substitute a GPT-2 activation and produce a measurable change in a specified next-token logit margin while passing a self-patch identity control. It **does not** establish a generally meaningful mechanistic circuit or explain all of GPT-2's behavior.

The earlier default experiment patched position 1, which held the *same* token in both inputs; measured recovery was **0.0**. Moving the intervention to the differing position 2 yielded a measurable effect. This is a controlled engineering smoke test, not evidence that the chosen token pair constitutes a meaningful scientific task.

Results were observed from one recorded CI run, not a statistical sample. Repeat across seeds, inputs, architectures, CPU/MPS settings and exact dependency versions before interpreting sensitivity as robust. M3 assertion-based CI replay remains unimplemented.
