"""Trusted local subprocess entrypoint; newline-delimited request/result JSON.

The parent supplies validated GPT-2 parameters through stdin. Errors are
reported by class only; model stdout and stderr are discarded by the parent.
Only one request at a time is processed in this single subprocess.
"""

from __future__ import annotations

import contextlib
import json
import sys

from cortex_engine.pairing import run_gpt2_pair


def main() -> int:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or request.get("command") != "pair":
                raise ValueError("Unknown command")
            args = request.get("args")
            if not isinstance(args, dict):
                raise ValueError("Invalid experiment arguments")
            # Hugging Face/progress messages must never corrupt JSON stdout.
            with contextlib.redirect_stdout(sys.stderr):
                output = run_gpt2_pair(**args)
            response = {"kind": "result", "data": output}
        except Exception as exc:
            # Do not echo private user prompts or exception text.
            response = {"kind": "error", "error_type": type(exc).__name__}
        try:
            sys.stdout.write(json.dumps(response, allow_nan=False) + "\n")
            sys.stdout.flush()
        except (OSError, ValueError):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
