# M4 — Browser regression authoring, E2E and recovery

## Status

M4 adds an in-browser **review and download** workflow for a versioned
regression manifest, Playwright Chromium E2E coverage, and a worker restart
safety fix. Browser integration with mocked API responses was verified: [3/3 E2E pass](https://github.com/parksy1625/cortex-debugger/actions/runs/39996800312).

## Workflow

1. Run both local services (see README). Execute a paired GPT-2 experiment.
2. When its model output reports `pass`, choose **Prepare regression test**.
3. Cortex checks the saved submitted prompts against the result's SHA-256
   fingerprints, exact model revision, device and intervention coordinate.
4. Review the proposed numeric tolerances; edit the thresholds if appropriate.
5. Choose **Download regression JSON** and use
   `cortex validate your-file.json` and `cortex verify your-file.json`
   locally or in CI.

**Important privacy property:** A manifest *contains RAW PROMPTS*. No raw
prompts are persisted in SQLite or reconstructed from History; the in-memory
submission is only available during the current browser session. No private
manifest is uploaded to GitHub automatically. Do not commit private prompts.

Automatic proposed bounds (not statistical confidence intervals) start from
observed measurements with a minimum 0.15 absolute margin, approximately
25% relative width for recovery and 30% for patched logit margin. These are
UI starting points, not scientific limits. All fields can be edited and invalid
ranges block the download.

The browser can only generate manifests from the recognized pinned GPT-2
revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`; an experiment using a
different revision cannot silently produce a bogus validated reference.

## Browser tests

```bash
cd apps/web
npm install
npx playwright install chromium
npm run test:e2e
```

Playwright intercepts local API requests, so tests run without downloading
GPT-2. Tests check experiment status, RMS cell display, numeric scores,
hash-verified manifest export, hash mismatch rejection and lack of prompt
recovery from History. This tests **UI and protocol integration**, not the
actual PyTorch inference engine, which is covered by the separate pinned
model regression CI.

## Restart recovery

The API worker marks previous `queued` or `running` jobs as `failed`
when it starts. It cannot safely resume old in-flight inference because
original raw prompts are intentionally not persisted. This avoids endlessly
polling orphaned jobs. No safe mid-inference cancellation or hard timeout yet.

## Apple Silicon / MPS: validated on GitHub's ARM64 macOS runner

On a Mac with compatible PyTorch MPS:

```bash
pip install -e '.[ml]'
cortex smoke --device mps --layer 0 --token-index 0
cortex pair --clean 'The dog runs' --corrupted 'The cat runs' \
  --correct-token ' dog' --incorrect-token ' cat' \
  --layer 5 --token-index 2 --device mps \
  --output artifacts/apple-mps-example.json
```

The pinned GPT-2 smoke and paired activation patch passed on real Apple Silicon
([workflow #39996476238](https://github.com/parksy1625/cortex-debugger/actions/runs/39996476238)).
See [CPU vs MPS measured values](M4_VALIDATION.md); do not assume parity
for other models, prompts, dtype settings or execution environments.

## Known gaps

- Full browser E2E against a real GPT-2 backend is not covered by mocked E2E.
- Browser runs do not share model state with CI and MPS is not tested.
- Hard model timeouts, memory budgets, dependency lockfiles, API authentication
  for remote use, signed artifacts and browser-accessible full regression replay
  remain future scope.
