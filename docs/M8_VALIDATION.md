# M8 validation — 2026-10-24 KST

## What GitHub verified

- [M8 bundle smoke run #40010730964](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730964): **SUCCESS**.
- [Python/React quality run #40010730772](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730772): **96 Python tests passed**, one opt-in real-model unit test skipped, Ruff clean, production React build passed.
- [Browser E2E run #40010730765](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730765): **SUCCESS**.
- [Real GPT-2 API/browser source-stack #40010730773](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730773): **SUCCESS**.
- [Pinned GPT-2 regression #40010730778](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730778): consult workflow result for that commit.

The bundle job built a **pure-Python core wheel**, compiled the React
UI, assembled `Cortex-Debugger-v0.9.0-rc1.zip`, verified its SHA-256,
extracted the same ZIP into a fresh temporary folder, installed bundled
engine dependencies in a new virtualenv and launched its **packaged**
`apps.api.main` on `127.0.0.1:8000`. An actual Playwright Chrome
session ran a paired GPT-2 experiment through the packaged UI and API and
downloaded a regression manifest. The browser release test **passed**.

Test archive: [Actions artifact #12526621073](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730964/artifacts/12526621073),
name `Cortex-Debugger-v0.9.0-rc1`. This is an **artifact wrapper**
containing the runtime ZIP and its SHA-256 file, not an MSI/DMG installer.
Actions artifacts expire. The tag-gated/passing-main release step
publishes a GitHub prerelease only after a fresh successful ZIP smoke test.

## Packaging limitations

- Actual packaged runtime verified on one GitHub-hosted Linux x86-64 runner.
  ZIP launcher scripts for macOS and Windows are not yet validated on those OSes.
- Users need Python 3.11+ and an internet connection for downloading
  first-run PyTorch/TransformerLens deps and GPT-2 weights. Only the engine
  wheel and compiled web assets are shipped.
- The server is bound to local loopback and has no authentication. Never
  expose to a public interface or a multi-user environment.
- SHA-256 allows byte-integrity checking but **does not authenticate
  the release as a trusted signer**. Code signatures, notarization and
  supply-chain attestations remain unfinished.
- Full evidence may reveal token IDs; manifests include raw prompts; SQLite
  record deletion does not erase historical backups/journals.
