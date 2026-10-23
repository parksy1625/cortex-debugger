# M4 verified evidence — October 24, 2026 (Asia/Seoul)

## GitHub Actions outcomes

| Pipeline | Result | Evidence |
| --- | --- | --- |
| 77 Python unit/integration tests and React production build | Pass | [run #39995932741](https://github.com/parksy1625/cortex-debugger/actions/runs/39995932741) |
| Real pinned GPT-2 CPU regression replay | Pass | [run #39995808419](https://github.com/parksy1625/cortex-debugger/actions/runs/39995808419) |
| Playwright browser E2E with mocked backend | **3/3 pass** | [run #39996800312](https://github.com/parksy1625/cortex-debugger/actions/runs/39996800312) |
| GPT-2 on genuine Apple Silicon MPS runner | Pass | [run #39996476238](https://github.com/parksy1625/cortex-debugger/actions/runs/39996476238) |

The MPS validation was performed by GitHub Actions on a **macos-15** standard
Apple Silicon machine (not a personal Mac mini). Exact model revision:
`607a30d783dfa663caf39e06633721c8d4cfcd7e`.

## Measured CPU vs MPS — one paired-prompt sample

Sample `The dog runs` → `The cat runs`, layer 5, token index 2,
correct token ` dog`, incorrect ` cat`, TransformerLens 4.2.0.
Measures are **local numerical effects**, not model-wide causal descriptions.

| Measurement | Linux CPU | Apple Silicon MPS |
| --- | ---: | ---: |
| Self patch max absolute logit difference | 0.0 | 0.0 |
| Clean next-token logit margin | 0.8115386963 | 0.8115844727 |
| Corrupted margin | -0.3125610352 | -0.3125915527 |
| Patched margin | 0.8504791260 | 0.8504943848 |
| Normalized recovery | 1.0346414367 | 1.0346119391 |

The absolute difference in recovery is approximately 0.0000295
(0.00295 percentage points). This is *one example* and not an
across-hardware parity guarantee or benchmark.

Mac hosted runner self-patch command took 14.935s and paired-prompt
command reported 2.921s, which includes environment-dependent work.
Do not compare these times directly to different Linux runner measurements
or interpret them as representative throughput.

MPS result artifact: `cortex-mps-validation`, ID `12519802581`,
accessible from the run page until GitHub's artifact expiry.
The Playwright E2E tests use mocked API responses; no Python server or
model weights are loaded by these browser tests.

## Fixed bugs surfaced by CI

- M4 bumped API stage to `M4`, so the health-check test expectation
  was updated; Python quality rerun passed 77 tests.
- First browser E2E run discovered downloaded manifest JSON had a
  literal `\\n` suffix. Removed the malformed suffix and reran:
  three browser tests passed, including parsing the downloaded file.

## Remaining risks

- End-to-end *browser + real GPT-2* integration still not separately automated.
- Only one small pinned GPT-2 experiment was compared CPU vs MPS.
- No reproducible dependency lockfiles or cryptographically signed execution provenance.
- No hard inference timeout, live model-task cancellation or model-session reuse guarantee.
- GitHub required branch checks have not been configured via admin controls.
- Manifest downloads include raw prompts; care is needed when sharing them.
