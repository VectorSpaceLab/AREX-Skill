#!/usr/bin/env python3
"""Preflight Nerfstudio config/output artifacts without loading a model.

Examples:
    python check_artifacts.py --config outputs/scene/nerfacto/run/config.yml --output-path metrics.json
    python check_artifacts.py --config config.yml --output-dir exports --require-existing-output-dir
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def scan_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf8", errors="ignore")
    except Exception as exc:
        raise SystemExit(f"Could not read {path}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check config.yml and output path readiness without loading Nerfstudio.")
    parser.add_argument("--config", type=Path, required=True, help="Path to a saved Nerfstudio config.yml.")
    parser.add_argument("--output-path", type=Path, help="Output file path to validate, e.g. metrics.json or render.mp4.")
    parser.add_argument("--output-dir", type=Path, help="Output directory to validate for exports/renders.")
    parser.add_argument("--require-existing-output-dir", action="store_true", help="Fail if output directory does not already exist.")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []

    if not args.config.exists():
        failures.append(f"config not found: {args.config}")
    elif args.config.name not in {"config.yml", "config.yaml"}:
        warnings.append("config filename is not config.yml/config.yaml; verify this is a saved run config")

    if args.config.exists():
        text = scan_text(args.config)
        for token in ["method_name", "pipeline", "datamanager", "model"]:
            if token not in text:
                warnings.append(f"config text does not contain expected token {token!r}")
        # Heuristic extraction of path-like values that may need checking.
        for match in re.finditer(r"(?:data|load_dir|load_config|checkpoint|ckpt_path):\s*([^\n]+)", text):
            value = match.group(1).strip().strip("'\"")
            if value and not value.startswith(("null", "None")):
                print(f"config reference: {match.group(0).strip()}")

    for out in [args.output_path, args.output_dir]:
        if out is None:
            continue
        parent = out if args.output_dir and out == args.output_dir else out.parent
        if args.require_existing_output_dir and not parent.exists():
            failures.append(f"output directory does not exist: {parent}")
        elif not parent.exists():
            warnings.append(f"output parent does not exist yet and will need to be created: {parent}")
        if parent.exists() and not parent.is_dir():
            failures.append(f"output parent is not a directory: {parent}")

    if args.output_path and args.output_path.suffix == "":
        warnings.append("output path has no suffix; ensure the selected command accepts a directory or extensionless file")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if failures:
        print("Failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Artifact preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
