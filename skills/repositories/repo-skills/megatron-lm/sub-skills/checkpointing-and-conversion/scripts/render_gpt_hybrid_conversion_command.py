#!/usr/bin/env python3
"""Render a Megatron GPT/Hybrid checkpoint conversion command template."""

from __future__ import annotations

import argparse
import re

_ALLOWED = set("M*-EGD|/")


def validate_pattern(pattern: str) -> list[str]:
    issues: list[str] = []
    bad = sorted(set(pattern) - _ALLOWED)
    if bad:
        issues.append(f"unsupported characters: {bad}")
    main = pattern.split("/", 1)[0].replace("|", "")
    attn = main.count("*")
    mlp = main.count("-") + main.count("E")
    if attn == 0 or mlp == 0:
        issues.append("pattern should contain at least one attention '*' and one MLP '-' or 'E' position")
    if attn != mlp:
        issues.append(f"attention positions ({attn}) do not match MLP-bearing positions ({mlp})")
    if "G" in main or "D" in main:
        issues.append("G/D symbols are not GPT-compatible converter targets")
    if "-" in main and "E" in main:
        issues.append("mixing dense '-' and MoE 'E' MLP positions is usually rejected for GPT-compatible conversion")
    if not re.fullmatch(r"[M*\-EGD|/]+", pattern):
        issues.append("pattern contains unexpected syntax")
    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="Render a gpt_hybrid_conversion.py command.")
    p.add_argument("--direction", choices=["gpt-to-hybrid", "hybrid-to-gpt"], required=True)
    p.add_argument("--load-dir", required=True)
    p.add_argument("--save-dir", required=True)
    p.add_argument("--hybrid-layer-pattern", required=True)
    p.add_argument("--input-format", default="auto", choices=["auto", "torch_dist", "fsdp_dtensor"])
    p.add_argument("--output-format", default="auto", choices=["auto", "torch_dist", "fsdp_dtensor"])
    p.add_argument("--d-model", type=int, default=None)
    p.add_argument("--reset-iterations", action="store_true")
    args = p.parse_args()

    issues = validate_pattern(args.hybrid_layer_pattern)
    if issues:
        print("Pattern warnings:")
        for issue in issues:
            print(f"- {issue}")
        print()

    parts = [
        "python tools/checkpoint/gpt_hybrid_conversion.py",
        f"  --direction {args.direction}",
        f"  --load-dir {args.load_dir}",
        f"  --save-dir {args.save_dir}",
        f"  --hybrid-layer-pattern '{args.hybrid_layer_pattern}'",
        f"  --input-format {args.input_format}",
        f"  --output-format {args.output_format}",
    ]
    if args.d_model is not None:
        parts.append(f"  --d-model {args.d_model}")
    if args.reset_iterations:
        parts.append("  --reset-iterations")
    print(" \\\n".join(parts))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
