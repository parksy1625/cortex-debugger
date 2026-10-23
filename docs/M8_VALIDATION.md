# M8 validation — 2026-10-24 KST

## What GitHub verified

- [M8 bundle smoke run #40010730964](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730964): **SUCCESS**.
- [Python/React quality run #40010730772](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730772): **96 Python tests passed**, one opt-in real-model unit test skipped, Ruff clean, production React build passed.
- [Browser E2E run #40010730765](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730765): **SUCCESS**.
- [Real GPT-2 API/browser source-stack #40010730773](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730773): **SUCCESS**.
- [Pinned GPT-2 regression #40010730778](https://github.com/parksy1625/cortex-debugger/actions/runs/40010730778): **SUCCESS**.
- [Verified release publication #40011290473](https://github.com/parksy1625/cortex-debugger/actions/runs/40011290473): **SUCCESS**. Both the ZIP verification job and public prerelease publication job passed.
- [Published ZIP reinstalled on genuine Apple Silicon MPS #40011896404](https://github.com/parksy1625/cortex-debugger/actions/runs/40011896404): **SUCCESS**. SHA-256 verified, macOS `start.sh` bootstrapped a fresh Python environment, HTTP API and compiled UI served, PyTorch Metal backend detected, real GPT-2 patch completed.

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
Actions artifacts expire. The public [v0.9.0-rc1 prerelease](https://github.com/parksy1625/cortex-debugger/releases/tag/v0.9.0-rc1)
is now published with the same tested ZIP and checksum.
Verified asset SHA-256: `f24acfa4e13991bb3d8299ee445137072af7affa010cd501833569b2321ced2d`.

Apple Silicon MPS smoke reported normalized recovery
`1.0345988353942421` (~103.4599%) at layer 5/token 2, with an identity
control error under 1e-4. This validates **one pinned GPT-2 example on one
macOS hosted runner**, not all Mac systems or models.

## Packaging limitations

- Packaged runtime verified on GitHub-hosted Linux x86-64 (wheel+compiled UI+
  actual browser GPT-2) **and Apple Silicon macOS** (release ZIP+native
  bootstrap+actual GPT-2 MPS). Windows is still not validated.
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
