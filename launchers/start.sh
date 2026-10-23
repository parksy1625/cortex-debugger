#!/usr/bin/env bash
set -euo pipefail

# Standalone source/runtime bundle; model weights and Python dependencies
# download on first use. Always listen on loopback only.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
VENV="$ROOT/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON=python3.11
  else
    PYTHON=python3
  fi
  "$PYTHON" -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
  "$PYTHON" -m venv "$VENV"
fi

WHEEL="$(find "$ROOT/wheel" -maxdepth 1 -type f -name 'cortex_debugger-*.whl' -print -quit)"
if [[ -z "$WHEEL" ]]; then
  echo "Cortex package wheel missing from bundle." >&2
  exit 2
fi

if [[ ! -f "$VENV/.cortex-m8-ready" ]]; then
  "$VENV/bin/python" -m pip install --upgrade pip
  if [[ "$(uname -s)" == "Linux" ]]; then
    # Official CPU wheel prevents a large unrequested CUDA toolchain.
    "$VENV/bin/python" -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cpu
    "$VENV/bin/python" -m pip install "${WHEEL}[ml,api]" -c "$ROOT/requirements-linux-py311.lock"
  else
    # On Apple Silicon install a macOS-native PyTorch wheel; do not apply a
    # Linux-only environment lock to macOS.
    "$VENV/bin/python" -m pip install 'torch==2.7.1'
    "$VENV/bin/python" -m pip install "${WHEEL}[ml,api]"
  fi
  touch "$VENV/.cortex-m8-ready"
fi

echo "Cortex Debugger local app: http://127.0.0.1:8000/"
echo "Ctrl+C to stop. No network interface is exposed."
exec "$VENV/bin/python" -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
