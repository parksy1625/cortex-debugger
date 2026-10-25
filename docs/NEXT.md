# After M10 browser-origin protections and setup diagnostics

1. Validate same-origin compiled UI, explicit Vite origin opt-in and
   hostile Host/Origin/Fetch-Site requests via GitHub Actions.
2. Implement **actual owner-bound local authorization** using process-held
   credential bootstrap or authenticated IPC. Host/Origin checks are not auth.
3. Add download/install progress into Windows/Mac launcher UI and recovery
   diagnostics (but never log raw prompts).
4. Build v0.10 prerelease from current code; do NOT overwrite the already
   tested v0.9.0-rc1 binaries or reuse their version tag.
5. Add trusted publisher code signing, Apple notarization, Windows MSI,
   verified artifact provenance and native GUI click tests.
6. Add IPC response size guard, OS hard memory budgets and secure retention.
