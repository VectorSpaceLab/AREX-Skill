#!/usr/bin/env python3
"""Build a dry-run Qwen benchmark command without downloading or evaluating."""
from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="Build a Qwen evaluation command plan.")
    p.add_argument("--benchmark", required=True, choices=["ceval", "mmlu", "cmmlu", "gsm8k", "humaneval", "plugin"])
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--input")
    p.add_argument("--output")
    p.add_argument("--chat", action="store_true")
    p.add_argument("--use-fewshot", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    script_map = {
        "ceval": "eval/evaluate_chat_ceval.py" if args.chat else "eval/evaluate_ceval.py",
        "mmlu": "eval/evaluate_chat_mmlu.py" if args.chat else "eval/evaluate_mmlu.py",
        "cmmlu": "eval/evaluate_cmmlu.py",
        "gsm8k": "eval/evaluate_chat_gsm8k.py" if args.chat else "eval/evaluate_gsm8k.py",
        "humaneval": "eval/evaluate_chat_humaneval.py" if args.chat else "eval/evaluate_humaneval.py",
        "plugin": "eval/evaluate_plugin.py",
    }
    script = script_map[args.benchmark]
    parts = ["python", script, "-c", args.checkpoint]
    if args.input:
        if args.benchmark in {"gsm8k", "humaneval"}:
            parts += ["-f", args.input]
        else:
            parts += ["-d", args.input]
    if args.output and args.benchmark in {"gsm8k", "humaneval"}:
        parts += ["-o", args.output]
    if args.use_fewshot:
        parts.append("--use-fewshot")
    if args.overwrite:
        parts.append("--overwrite")
    if args.benchmark == "plugin":
        parts = ["python", script, "-c", args.checkpoint, "--eval-react-positive", "--eval-react-negative", "--eval-hfagent"]
    print("DRY RUN (not executed):")
    print(" ".join(parts))
    print("Prerequisites: benchmark dataset/layout, checkpoint family, and any sandbox or extra packages the benchmark requires.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
