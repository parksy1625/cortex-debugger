# M9 — Native launchers and cross-platform smoke validation

M9 separates two goals: **platform-tested bootstrap reliability** and
**native-looking application launch**. The released M8 runtime is still
the dependency/bootstrap payload. Users must install Python 3.11+ and
download PyTorch/TransformerLens/GPT-2 on first use.

## Windows x64

The `Windows published ZIP native smoke` workflow downloads the **public
v0.9.0-rc1 release**, verifies its SHA-256, extracts it on a Windows runner,
launches the bundled `start.ps1`, boots the local server and executes the
canonical GPT-2 patch through its HTTP API. This **passed** in [M9 Windows CI](https://github.com/parksy1625/cortex-debugger/actions/runs/40016740044).

The workflow also builds a **.NET 8 self-contained Windows Forms GUI launcher**,
combines `CortexDebugger.exe` with a fresh copy of the same release runtime,
performs a headless `--self-test` of the final EXE, and publishes a SHA-256-
checked portable Windows ZIP. The GUI provides Start / Stop / Open browser
actions and is styled as a compact dark local control panel. The graphical
button interactions themselves are **not verified in headless CI**.

This is PowerShell/CPU bootstrap plus a compiled GUI launcher, not an MSI,
code-signed app, or offline installer. The runtime uses one process, listens only on 127.0.0.1 and
does not expose an internet-facing API.

## macOS Finder .app

`scripts/build_macos_app.py` transforms the published ZIP into an unsigned
`Cortex Debugger.app` directory. The native Finder/LaunchServices container
has `Info.plist`, executable launcher and the precompiled M8 runtime under
`Contents/Resources/runtime`.

On first run, the launcher copies the runtime to
`~/Library/Application Support/Cortex Debugger/v0.9.0-rc1`, so dependency
installation does not need write access inside `/Applications`.
It starts a visible Terminal window that runs `start.sh`, waits for
the loopback API to become ready, and opens the browser UI.

A macOS ARM64 GitHub workflow builds the Finder container, exercises its
executable non-interactively against an isolated user runtime directory,
and then executes real MPS GPT-2 inference. This [macOS app workflow](https://github.com/parksy1625/cortex-debugger/actions/runs/40015722520)
**passed**, and a zipped `.app` and SHA-256 checksum were added to the
[v0.9.0-rc1 GitHub Release](https://github.com/parksy1625/cortex-debugger/releases/tag/v0.9.0-rc1).

**Not a standalone/offline native binary:** this .app is a Finder launcher,
not a fully bundled Python/Torch executable. It is unsigned and
not notarized; Gatekeeper may prevent opening it without an explicit
user trust decision. Finder UI and AppleScript Terminal interaction itself
are not automatically verified in the headless CI test — CI calls the
same app executable using `CORTEX_TEST_LAUNCH=1`.

## Security and remaining work

- The released ZIP is pinned and checksummed; SHA-256 detects changes but is
  not a software publisher signature.
- No arbitrary untrusted model code should run inside this process.
- Raw regression manifests contain prompts and evidence may contain tokens.
- Windows MSI, truly self-contained macOS builds, code signing and
  notarization, per-platform locks and updater/rollback remain milestones.
- No public interface exposed; however a malicious local process can reach
  this unauthenticated loopback API. Not suitable for adversarial multi-user environments.
