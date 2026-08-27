#!/usr/bin/env python3
"""Build a TurboDiffusion modify_model.py command without executing it."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


PROFILES = {
    "t2v-1.3b-480p": {
        "model": "Wan2.1-1.3B",
        "input": "checkpoints/1.3B_ckpts/2_1_480P/merge_rcm_format.pth",
        "output": "checkpoints/modified/TurboWan2.1-T2V-1.3B-480P.pth",
    },
    "t2v-14b-480p": {
        "model": "Wan2.1-14B",
        "input": "checkpoints/14B_ckpts/2_1_480P/merge_rcm_format.pth",
        "output": "checkpoints/modified/TurboWan2.1-T2V-14B-480P.pth",
    },
    "t2v-14b-720p": {
        "model": "Wan2.1-14B",
        "input": "checkpoints/14B_ckpts/2_1_720P/merge_rcm_format.pth",
        "output": "checkpoints/modified/TurboWan2.1-T2V-14B-720P.pth",
    },
    "i2v-a14b-low-720p": {
        "model": "Wan2.2-A14B",
        "input": "checkpoints/14B_ckpts/2_2_720P/merged_low_noise.pth",
        "output": "checkpoints/modified/TurboWan2.2-I2V-A14B-low-720P.pth",
    },
    "i2v-a14b-high-720p": {
        "model": "Wan2.2-A14B",
        "input": "checkpoints/14B_ckpts/2_2_720P/merged_high_noise.pth",
        "output": "checkpoints/modified/TurboWan2.2-I2V-A14B-high-720P.pth",
    },
}

MODEL_CHOICES = ["Wan2.1-1.3B", "Wan2.1-14B", "Wan2.2-A14B"]


def q(value: object) -> str:
    return shlex.quote(str(value))


def quantized_output_name(path: str) -> str:
    p = Path(path)
    stem = p.stem
    if stem.endswith("-quant"):
        return str(p)
    return str(p.with_name(stem + "-quant" + p.suffix))


def render_command(env: list[tuple[str, str]], argv: list[str], one_line: bool) -> str:
    tokens = [f"{key}={q(value)}" for key, value in env] + [q(part) for part in argv]
    if one_line:
        return " ".join(tokens)
    lines: list[str] = []
    if env:
        lines.append(" ".join(tokens[: len(env)]) + " \\")
        rest = tokens[len(env) :]
    else:
        rest = tokens
    for i, token in enumerate(rest):
        suffix = " \\" if i < len(rest) - 1 else ""
        lines.append("  " + token + suffix)
    return "\n".join(lines)


def validate_inputs(input_path: str, output_path: str) -> int:
    errors: list[str] = []
    if not Path(input_path).exists():
        errors.append(f"missing input_path: {input_path}")
    parent = Path(output_path).parent
    if str(parent) and not parent.exists():
        errors.append(f"output parent directory does not exist: {parent}")
    if errors:
        print("Input validation failed:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        return 2
    print("Input validation passed.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboDiffusion inference/modify_model.py export command. "
            "This helper only prints a command; it does not load checkpoints, use CUDA, or write output."
        )
    )
    parser.add_argument(
        "--profile",
        choices=["custom", *PROFILES.keys()],
        default="t2v-1.3b-480p",
        help="Fill public model/input/output defaults for a common checkpoint role.",
    )
    parser.add_argument("--model", choices=MODEL_CHOICES, help="Override model name passed to --model.")
    parser.add_argument("--input-path", help="Override input rCM/SLA checkpoint path.")
    parser.add_argument("--output-path", help="Override output modified checkpoint path.")
    parser.add_argument("--attention-type", choices=["original", "sla", "sagesla"], default="sla")
    parser.add_argument("--sla-topk", type=float, default=0.2)
    parser.add_argument("--quant-linear", action="store_true", help="Add --quant_linear for INT8 linear export.")
    parser.add_argument(
        "--keep-default-norms",
        action="store_true",
        help="Add --default_norm, which keeps default norm layers instead of FastNorm replacement.",
    )
    parser.add_argument("--python", default="python", help="Python executable name/path.")
    parser.add_argument("--package-source-dir", default="turbodiffusion", help="Source-layout package directory for PYTHONPATH/script defaults.")
    parser.add_argument("--script-path", help="Override modify_model.py path.")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prefix command with PYTHONPATH.")
    parser.add_argument("--validate-inputs", action="store_true", help="Check input and output parent paths without running conversion.")
    parser.add_argument("--one-line", action="store_true", help="Print command on one line.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.profile == "custom":
        defaults = {
            "model": "Wan2.1-1.3B",
            "input": "checkpoints/merge_rcm_format.pth",
            "output": "checkpoints/modified/TurboDiffusion-modified.pth",
        }
    else:
        defaults = PROFILES[args.profile]

    model = args.model or defaults["model"]
    input_path = args.input_path or defaults["input"]
    output_path = args.output_path or defaults["output"]
    if args.quant_linear and args.output_path is None:
        output_path = quantized_output_name(output_path)
    script_path = args.script_path or str(Path(args.package_source_dir) / "inference" / "modify_model.py")

    if args.validate_inputs:
        status = validate_inputs(input_path, output_path)
        if status:
            return status

    env: list[tuple[str, str]] = []
    if not args.no_pythonpath:
        env.append(("PYTHONPATH", args.package_source_dir))

    argv = [
        args.python,
        script_path,
        "--input_path",
        input_path,
        "--output_path",
        output_path,
        "--model",
        model,
        "--attention_type",
        args.attention_type,
        "--sla_topk",
        str(args.sla_topk),
    ]
    if args.quant_linear:
        argv.append("--quant_linear")
    if args.keep_default_norms:
        argv.append("--default_norm")

    print(render_command(env, argv, args.one_line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
