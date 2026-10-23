# M8 packaging architecture and release validation

The M8 pre-release is a **local ZIP bootstrap distribution**, not an
offline installer or standalone binary.

The ZIP includes: the pure Python engine wheel, FastAPI service modules,
precompiled React/Vite web assets, per-OS launch scripts, Linux 3.11 pinned
version constraints, LICENSE, and usage notes. Python 3.11+ must be installed
separately; on first launch the script creates a virtualenv and downloads
Torch/TransformerLens dependencies and pinned GPT-2 model weights.

## Runtime design

`apps.api.main` mounts compiled UI files at `/` **after** the API routes,
so a single localhost port handles React and REST. Source-only development
still uses Vite when no built static assets exist.

The engine wheel is installed from the ZIP. API modules are distributed as
source alongside it, because this project currently packages the core engine
wheel separately. Start scripts set the working directory to the ZIP root
so the isolated child subprocess can also import `apps.api.model_worker`.

## Artifact test and tag-gated publication

GitHub Actions build steps:
1. Build Python wheel using `python -m build --wheel`.
2. `npm ci` + production Vite React build.
3. Assemble ZIP with an explicit file allowlist and compute SHA-256.
4. Extract the ZIP to a *fresh* path; pip install its wheel into a new
   virtualenv using CPU torch 2.7.1 and Linux-specific constraints.
5. Start the **packaged** FastAPI service and fetch compiled UI and API health.
6. Run existing real GPT-2 Chromium E2E against **port 8000**, not Vite.
7. Upload the verified ZIP and checksum as an Actions artifact.
8. Publish the same ZIP as a GitHub prerelease only when the exact tag
   `v0.9.0-rc1` is pushed and the package smoke job succeeds.

The release pipeline currently does **not** sign/notarize the macOS binary,
use OS-native executable installers, provide user credential management or
supply-chain attestations. macOS and Windows launcher paths are prepared but
have not been validated in platform-specific CI.

## Safety limitations

The local API has no authentication or network rate limiting: start scripts
bind `127.0.0.1` only. Raw regression manifests contain literal prompts.
Aggregated redacted output may still reveal details. SQLite deletion is not
secure removal of old journal/backup bytes. Nothing in this local package
constitutes a security sandbox for arbitrary untrusted models.
