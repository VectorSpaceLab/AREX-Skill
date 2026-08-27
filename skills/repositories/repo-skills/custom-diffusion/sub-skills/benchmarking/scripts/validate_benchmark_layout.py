#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

def _read_prompts(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("prompts.json must be a JSON object")
    return {str(key): str(value) for key, value in data.items()}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a CustomConcept101 sample folder layout.")
    parser.add_argument("--sample-root", required=True, help="Root directory that contains samples/ and prompts.json.")
    parser.add_argument("--numgen", type=int, required=True, help="Expected number of generated PNG files.")
    parser.add_argument("--prompts-json", default=None, help="Optional explicit path to prompts.json.")
    parser.add_argument("--target-paths", default="", help="+ separated benchmark target paths.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    sample_root = Path(args.sample_root)
    sample_dir = sample_root / "samples"
    prompts_path = Path(args.prompts_json) if args.prompts_json else sample_root / "prompts.json"

    errors: list[str] = []
    if not sample_dir.is_dir():
        errors.append(f"missing samples directory: {sample_dir}")
    pngs = sorted(sample_dir.glob("*.png")) if sample_dir.is_dir() else []
    stems = [path.stem for path in pngs]
    if len(pngs) != args.numgen:
        errors.append(f"expected {args.numgen} PNG files, found {len(pngs)}")

    try:
        prompts = _read_prompts(prompts_path)
    except Exception as exc:
        errors.append(str(exc))
        prompts = {}

    if set(prompts.keys()) != set(stems):
        missing = sorted(set(stems) - set(prompts.keys()))
        extra = sorted(set(prompts.keys()) - set(stems))
        if missing:
            errors.append(f"prompts.json is missing stems: {missing[0]}")
        if extra:
            errors.append(f"prompts.json has extra keys: {extra[0]}")

    target_segments = [segment for segment in args.target_paths.split("+") if segment]
    if args.target_paths and not target_segments:
        errors.append("target_paths contains only empty segments")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    summary = {
        "sample_root": str(sample_root),
        "png_count": len(pngs),
        "prompt_count": len(prompts),
        "target_count": len(target_segments),
    }
    print(summary)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
