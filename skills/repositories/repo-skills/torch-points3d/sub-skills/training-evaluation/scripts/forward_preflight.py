#!/usr/bin/env python3
"""Preflight a Torch Points3D checkpoint forward-inference job.

This helper validates paths and runtime intentions before a forward script loads
models, creates datasets, or writes prediction `.npy` files. It does not import
Torch Points3D or touch checkpoint contents.

Example:
  python sub-skills/training-evaluation/scripts/forward_preflight.py \
    --checkpoint-dir /runs/2021-01-01/12-00-00 --model-name pointnet2_charlesssg \
    --input-path /data/unlabeled --output-path ./predictions
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check file-system prerequisites for Torch Points3D forward inference.")
    parser.add_argument("--checkpoint-dir", required=True, type=Path, help="Directory containing <model-name>.pt.")
    parser.add_argument("--model-name", required=True, help="Checkpoint basename without .pt.")
    parser.add_argument("--weight-name", default="latest", help="Weight key to load, usually latest or a metric token.")
    parser.add_argument("--input-path", required=True, type=Path, help="Input dataset/root path for forward data.")
    parser.add_argument("--output-path", required=True, type=Path, help="Directory where predictions should be written.")
    parser.add_argument("--create-output", action="store_true", help="Create output directory if it does not exist.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    problems = []
    checkpoint_file = args.checkpoint_dir / f"{args.model_name}.pt"

    if not args.checkpoint_dir.is_dir():
        problems.append(f"checkpoint-dir is not a directory: {args.checkpoint_dir}")
    elif not checkpoint_file.is_file():
        available = sorted(p.name for p in args.checkpoint_dir.glob("*.pt"))
        problems.append(f"checkpoint file missing: {checkpoint_file}; available .pt files: {available}")

    if not args.input_path.exists():
        problems.append(f"input-path does not exist: {args.input_path}")

    if args.output_path.exists() and not args.output_path.is_dir():
        problems.append(f"output-path exists but is not a directory: {args.output_path}")
    elif not args.output_path.exists():
        if args.create_output:
            args.output_path.mkdir(parents=True, exist_ok=True)
        else:
            parent = args.output_path.parent
            if not parent.exists():
                problems.append(f"output parent does not exist: {parent}")
            else:
                problems.append("output-path does not exist; rerun with --create-output if this is intentional")

    result = {
        "status": "passed" if not problems else "failed",
        "checkpoint_file": str(checkpoint_file),
        "weight_name": args.weight_name,
        "input_path_exists": args.input_path.exists(),
        "output_path_exists": args.output_path.exists(),
        "problems": problems,
        "next_step": "Run the real forward script only after confirming dataset FORWARD_CLASS support and backend availability.",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Torch Points3D forward preflight: {result['status']}")
        for problem in problems:
            print("problem:", problem)
        if not problems:
            print("checkpoint:", checkpoint_file)
            print("input:", args.input_path)
            print("output:", args.output_path)
            print(result["next_step"])
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
