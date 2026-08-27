#!/usr/bin/env python3
"""Build a TurboDiffusion safetensors_to_pth.py command without executing it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path


INDEX_NAME = "diffusion_pytorch_model.safetensors.index.json"


def q(value: object) -> str:
    return shlex.quote(str(value))


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


def validate_layout(model_dir: str, output_path: str) -> int:
    errors: list[str] = []
    root = Path(model_dir)
    index_path = root / INDEX_NAME
    if not root.is_dir():
        errors.append(f"model_dir is not a directory: {model_dir}")
    if not index_path.is_file():
        errors.append(f"missing index file: {index_path}")
    weight_map = None
    if index_path.is_file():
        try:
            with index_path.open("r", encoding="utf-8") as handle:
                index = json.load(handle)
            weight_map = index.get("weight_map")
            if not isinstance(weight_map, dict) or not weight_map:
                errors.append(f"index has no non-empty weight_map: {index_path}")
        except Exception as exc:  # noqa: BLE001 - validation should report JSON failures plainly.
            errors.append(f"could not read index JSON {index_path}: {exc}")
    if isinstance(weight_map, dict):
        missing = sorted({str(name) for name in weight_map.values() if not (root / str(name)).is_file()})
        if missing:
            preview = ", ".join(missing[:5])
            more = "" if len(missing) <= 5 else f" ... (+{len(missing) - 5} more)"
            errors.append(f"missing safetensors shard files: {preview}{more}")
    parent = Path(output_path).parent
    if str(parent) and not parent.exists():
        errors.append(f"output parent directory does not exist: {parent}")

    if errors:
        print("Layout validation failed:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        return 2
    print("Layout validation passed.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboDiffusion sharded safetensors-to-PyTorch command. "
            "This helper only prints a command; it does not read tensors or write checkpoints."
        )
    )
    parser.add_argument("--model-dir", default="checkpoints/hf_model", help=f"Directory containing {INDEX_NAME} and shard files.")
    parser.add_argument("--output-path", default="checkpoints/converted/model.pth", help="Destination .pth path.")
    parser.add_argument("--prefix", default=None, help="Optional prefix to add to every state-dict key, e.g. net.")
    parser.add_argument("--python", default="python", help="Python executable name/path.")
    parser.add_argument("--package-source-dir", default="turbodiffusion", help="Source-layout package directory for PYTHONPATH/script defaults.")
    parser.add_argument("--script-path", help="Override safetensors_to_pth.py path.")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prefix command with PYTHONPATH.")
    parser.add_argument("--validate-layout", action="store_true", help="Check index JSON, shards, and output parent without conversion.")
    parser.add_argument("--one-line", action="store_true", help="Print command on one line.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.validate_layout:
        status = validate_layout(args.model_dir, args.output_path)
        if status:
            return status

    script_path = args.script_path or str(Path(args.package_source_dir) / "scripts" / "safetensors_to_pth.py")
    env: list[tuple[str, str]] = []
    if not args.no_pythonpath:
        env.append(("PYTHONPATH", args.package_source_dir))

    argv = [
        args.python,
        script_path,
        "--model_dir",
        args.model_dir,
        "--output_path",
        args.output_path,
    ]
    if args.prefix is not None:
        argv.extend(["--prefix", args.prefix])

    print(render_command(env, argv, args.one_line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
