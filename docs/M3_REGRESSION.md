# M3 — Causal Regression Tests (v0.4-dev)

## What is implemented

The `cortex verify` command **reruns** a pinned local GPT-2 experiment and
evaluates versioned, explicit numeric constraints. A previous saved JSON report
can be validated with `--artifact`, but that mode NEVER runs a model and
must not be misrepresented as live model verification.

The GitHub [Pinned model regression workflow](../.github/workflows/regression.yml)
reruns the model on a Linux CPU whenever the engine, manifest, dependency list
or workflow changes, and on PRs touching these files. A failing comparison gives
the Action a nonzero exit code, blocking a required status check once repository
branch protection is configured.

## Commands

```bash
pip install -e '.[ml,dev]'
cortex validate experiments/regression/gpt2-dog-cat.json

# Default: fresh GPT-2 inference at the manifest's exact pinned revision
cortex verify experiments/regression/gpt2-dog-cat.json \
  --report artifacts/regression-report.json \
  --junit artifacts/regression-junit.xml

# No inference: check an existing matching M2 experiment JSON artifact
cortex verify experiments/regression/gpt2-dog-cat.json \
  --artifact artifacts/model-smoke-pair.json \
  --report artifacts/offline-report.json
```

Exit codes: `0` = all checks passed, `1` = one or more assertions failed,
`2` = invalid manifest, missing model dependencies or verification error.

The schema-1 manifest uses only JSON to avoid implicit execution, requires
an exact known model commit SHA, allows CPU or MPS, and rejects unknown keys,
nonfinite metrics, invalid patch locations and missing behavioral assertions.
The control threshold must be >0 and <=0.1.

A valid verification checks **all** of these conditions:
- Model ID, exact commit SHA, device, patched layer and token position match.
- SHA256 hashes of the source and target prompts match the result metadata.
- Model execution status is `pass`.
- Self-patching numeric delta is within the declared maximum.
- Normalized recovery and patched logit margin satisfy configured bounds.

Reference example:
`experiments/regression/gpt2-dog-cat.json` targets a *mechanical*
GPT-2 dog/cat token example at layer 5, token position 2; it is not a validated
model circuit. Thresholds 0.75–1.35 recovery and 0.55–1.15 patched margin
are intended as loose smoke-regression guards, not scientifically justified
decision boundaries. The recorded baseline on 2026-10-24 was about 1.03464
recovery and 0.85048 patched margin; see [measured results](MEASURED_RESULTS.md).

## Privacy and security

Manifest files contain **raw prompts**. Do not commit confidential data or
real user prompts. Verification outputs, JUnit records, and failure messages
report metadata, numerical measurements, hashes and patch locations; they
should not emit the raw manifest prompts. M2 artifacts may contain token IDs
from which prompt information could be reconstructed.

Offline `--artifact` mode verifies the *contents* of evidence and can be
fabricated; it cannot authenticate that an actual model ran. Only CI logs or
trusted execution records can independently support a replay claim.

Model revisions other than the verified GPT-2 SHA are rejected by this
first version. Broader cross-version comparisons require independently
validated baselines.

## Remaining work

- Repeat confidence intervals across CPU/MPS, seeds, prompts and model changes.
- Exact environment/package lockfiles and recorded dtype+runtime metadata.
- Browser-native regression manifest authoring and CI link UI.
- GitHub branch protection (enable required check manually in repo settings).
- Atomic artifact writes, retention policy, signed provenance and failure
  recording for infrastructure crashes before the verifier returns.
