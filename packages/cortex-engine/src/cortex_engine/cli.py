"""Cortex CLI: model interventions and fail-closed regression verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

    pair = sub.add_parser("pair", help="Run clean/corrupted GPT-2 activation patch experiment")
    pair.add_argument("--clean", required=True)
    pair.add_argument("--corrupted", required=True)
    pair.add_argument("--correct-token", required=True)
    pair.add_argument("--incorrect-token", required=True)
    pair.add_argument("--layer", type=int, required=True)
    pair.add_argument("--token-index", type=int, required=True)
    pair.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    pair.add_argument("--revision", help="Hugging Face 40-character model commit SHA")
    pair.add_argument("--output", help="Save JSON report to file")

    validate = sub.add_parser("validate", help="Validate a strict pinned-model regression manifest")
    validate.add_argument("manifest", help="Path to schema-versioned JSON manifest")

    verify = sub.add_parser("verify", help="Replay model experiment; exit 1 if assertions fail")
    verify.add_argument("manifest", help="Path to schema-versioned JSON manifest")
    verify.add_argument("--artifact", help="Offline check of existing report (does NOT rerun model)")
    verify.add_argument("--report", help="Path to write assertion results JSON")
    verify.add_argument("--junit", help="Path to write JUnit XML for CI")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            output = {
                "version": __version__, "stage": "M10",
                "supported_models": ["openai-community/gpt2"],
                "commands": ["info", "score", "smoke", "pair", "validate", "verify"],
            }
        elif args.command == "score":
            output = {
                "recovery": recovery_score(args.clean, args.corrupted, args.patched),
                "clean_score": args.clean, "corrupted_score": args.corrupted,
                "patched_score": args.patched,
            }
        elif args.command == "pair":
            from cortex_engine.pairing import run_gpt2_pair

            if args.revision and (len(args.revision) != 40 or
                                  any(ch not in "0123456789abcdef" for ch in args.revision.lower())):
                raise ValueError("--revision must be a 40-character hexadecimal commit SHA")
            output = run_gpt2_pair(
                clean=args.clean, corrupted=args.corrupted,
                correct_token=args.correct_token, incorrect_token=args.incorrect_token,
                layer=args.layer, token_index=args.token_index, device=args.device,
                revision=args.revision,
            )
            if args.output:
                dest = Path(args.output)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        elif args.command == "validate":
            from cortex_engine.regression import load_manifest

            manifest = load_manifest(args.manifest)
            output = {"status": "valid", "schema_version": manifest["schema_version"],
                      "model_id": manifest["model"]["id"],
                      "revision": manifest["model"]["revision"],
                      "assertions": list(manifest["assertions"])}
        elif args.command == "verify":
            from cortex_engine.regression import load_manifest, verify, write_json, write_junit

            manifest = load_manifest(args.manifest)
            output = verify(manifest, artifact_path=args.artifact)
            if args.report:
                write_json(args.report, output)
            if args.junit:
                write_junit(args.junit, output)
        else:
            from cortex_engine.adapters.transformerlens import self_patch_smoke

            output = self_patch_smoke(
                prompt=args.prompt, device=args.device, layer=args.layer,
                token_index=args.token_index,
            )
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
        return 1 if output.get("status") == "fail" else 0
    except (RuntimeError, ValueError, ImportError, OSError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
