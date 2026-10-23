"""Cortex CLI proof-of-concept."""

from __future__ import annotations

import argparse
import json
import sys

from cortex_engine import __version__
from cortex_engine.metrics import recovery_score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cortex", description="Local-first model debugger")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="Print version and implemented capabilities")
    scores = sub.add_parser("score", help="Compute normalized causal-patching recovery")
    scores.add_argument("--clean", type=float, required=True)
    scores.add_argument("--corrupted", type=float, required=True)
    scores.add_argument("--patched", type=float, required=True)
    smoke = sub.add_parser("smoke", help="Download/load GPT-2 and test self-patching")
    smoke.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    smoke.add_argument("--layer", type=int, default=0)
    smoke.add_argument("--token-index", type=int, default=0)
    smoke.add_argument("--prompt", default="When Mary went to the store, she bought")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            output = {"version": __version__, "stage": "M0", "supported_models": ["openai-community/gpt2"]}
        elif args.command == "score":
            output = {
                "recovery": recovery_score(args.clean, args.corrupted, args.patched),
                "clean_score": args.clean, "corrupted_score": args.corrupted,
                "patched_score": args.patched,
            }
        else:
            from cortex_engine.adapters.transformerlens import self_patch_smoke

            output = self_patch_smoke(
                prompt=args.prompt, device=args.device, layer=args.layer,
                token_index=args.token_index
            )
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 1 if output.get("status") == "fail" else 0
    except (RuntimeError, ValueError, ImportError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
