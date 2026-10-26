#!/bin/bash
set -euo pipefail

# Finder entry point for the unsigned M12 source-runtime candidate on macOS.
# Keep the server in the visible Terminal session so the one-time pairing code
# can be read privately and Ctrl+C shuts it down.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Start-Cortex.command is for macOS. Use bash start.sh on Linux." >&2
  exit 2
fi
if [[ "${1:-}" != "--check" && ! -t 1 && -z "${CORTEX_PAIRING_CODE:-}" ]]; then
  echo "Open this file in a macOS Terminal window so you can read the one-time pairing code; or provide CORTEX_PAIRING_CODE via a trusted launcher." >&2
  exit 2
fi
cd "$ROOT"
exec /bin/bash "$ROOT/start.sh" "$@"
