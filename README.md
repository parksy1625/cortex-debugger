# Cortex Debugger

**Local-first activation-patching debugger, experiment studio and model regression gate.**

## M8 · v0.9.0-rc1 (release candidate)

M8 adds a **downloadable local ZIP** with a compiled React web UI, the
Python `cortex_engine` wheel, API runtime modules and cross-platform
bootstrap scripts. Users no longer need Node or the Vite dev server to use
the bundled app after downloading. The runtime creates a Python virtualenv
and downloads dependencies and GPT-2 model weights on first launch.
This is a **bootstrap bundle, not a self-contained/offline binary**.

### Install the local bundle

1. Get the `Cortex-Debugger-v0.9.0-rc1` ZIP from a passing
   [Local bundle and release](.github/workflows/bundle-release.yml) workflow
   artifact. If a matching tagged release has been published, use its Release
   asset and accompanying SHA-256 checksum.
2. Extract its contained `Cortex-Debugger-v0.9.0-rc1.zip`, then unpack the
   runtime ZIP into a folder.
3. On **macOS/Linux** run `bash start.sh`; on **Windows** run
   `powershell -ExecutionPolicy Bypass -File .\\start.ps1`.
4. Open **http://127.0.0.1:8000/** — web UI and API share the same origin.
   Keep the terminal running. Ctrl+C stops the server.

The bundled wheel and UI are packaged by GitHub Actions and an extracted
bundle is validated against **real GPT-2 inference using a browser** before
it can be uploaded as a verified release candidate.
See [M8 release guide](docs/M8_RELEASE.md) and
[M8 packaging architecture](docs/M8_PACKAGING.md).

The ZIP does **not** include model weights, downloaded Python packages,
or the Python interpreter itself. Internet access is needed on first install.
Only Linux x86-64 packaged execution is initially validated in Actions;
macOS/MPS and Windows scripts need independent packaged-run verification.

### Developer mode (source checkout)

```bash
python -m pip install -e '.[ml,api,dev]' -c requirements-linux-py311.lock
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/web
npm ci
npm run dev
# localhost:5173 (Vite -> API :8000)
```

Linux-only version constraints must **not** be used on Apple MPS or Windows.
PyTorch 2.7.1 CPU with the Linux Python 3.11 lockfile has been validated.
The pinned model revision is
`607a30d783dfa663caf39e06633721c8d4cfcd7e`.

### Scientific and privacy limitations

- The engine measures specified activation interventions and logit margins;
  a meaningful circuit is **not** proven merely by an intervention changing
  the output. Same-run self-patching controls and strict replay comparisons
  are included.
- Exported full evidence can include token IDs; manifests contain **raw
  prompts**. Redacted summaries exclude both but still reveal measurements.
- SQLite record deletion is not secure erasure of WAL, backups or snapshots.
- Server is unauthenticated. It is **localhost-only**; never expose it on a
  public/network interface or use multiple Uvicorn workers.
- CPU/MPS parity is supported by limited model-backed smoke evidence, not a
  cross-model benchmark; installer scripts for macOS/Windows remain unverified
  until their own CI runs.

Previous measured validation: [M7 report](docs/M7_VALIDATION.md) ·
[M6 subprocess isolation](docs/M6_VALIDATION.md).

MIT license.
