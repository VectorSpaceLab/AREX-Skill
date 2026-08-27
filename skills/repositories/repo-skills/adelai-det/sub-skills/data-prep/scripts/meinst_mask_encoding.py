#!/usr/bin/env python3
"""Plan/check MEInst mask-component generation inputs.

The full MEInst LME generation flow is data-heavy and lives in the package
source. This helper validates paths and prints a safe command plan.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MEInst mask encoding prerequisites")
    parser.add_argument("--repo-root", required=True, help="AdelaiDet source checkout root")
    parser.add_argument("--annotation-json", required=True, help="COCO annotation JSON with instance masks")
    parser.add_argument("--output-components", required=True, help="Target component directory")
    parser.add_argument("--mask-size", type=int, default=28)
    parser.add_argument("--dim-mask", type=int, default=60)
    parser.add_argument("--check-only", action="store_true", help="Only validate and print next steps")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    lme_dir = repo / "adet" / "modeling" / "MEInst" / "LME"
    ann = Path(args.annotation_json).resolve()
    out = Path(args.output_components).resolve()
    if not lme_dir.is_dir():
        raise SystemExit(f"missing MEInst LME directory: {lme_dir}")
    if not ann.exists():
        raise SystemExit(f"annotation JSON does not exist: {ann}")
    print(f"MEInst LME directory: {lme_dir}")
    print(f"annotation JSON: {ann}")
    print(f"component output: {out}")
    print(f"mask_size={args.mask_size} dim_mask={args.dim_mask}")
    print("Next: inspect mask_generation.py, MaskLoader.py, and config MODEL.MEInst.PATH_COMPONENTS before running a data-heavy generation job.")
    if not args.check_only:
        print("This helper does not run the heavy generation automatically; run the repository LME scripts only after confirming dataset size and budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
