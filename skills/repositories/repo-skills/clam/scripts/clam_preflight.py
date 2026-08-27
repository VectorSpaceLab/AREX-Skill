#!/usr/bin/env python3
"""Safe CLAM workflow preflight helper.

This helper validates path shapes and prints stage ownership for CLAM workflows.
It does not import CLAM, open WSI files, load checkpoints, train models, or write
outputs.
"""

from __future__ import annotations

import argparse
from pathlib import Path


STAGES = {
    "preprocessing": "sub-skills/wsi-preprocessing/SKILL.md",
    "features": "sub-skills/feature-extraction/SKILL.md",
    "training": "sub-skills/training-evaluation/SKILL.md",
    "evaluation": "sub-skills/training-evaluation/SKILL.md",
    "heatmaps": "sub-skills/heatmap-visualization/SKILL.md",
}


def existing_path(value: str | None) -> str:
    if not value:
        return "not provided"
    path = Path(value)
    return "exists" if path.exists() else "missing"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a safe CLAM workflow preflight checklist.")
    parser.add_argument("--stage", choices=sorted(STAGES), help="Workflow stage to route.")
    parser.add_argument("--slides-dir", help="Directory containing WSI files for preprocessing/features/heatmaps.")
    parser.add_argument("--patch-dir", help="Directory expected to contain fast-pipeline patch coordinate .h5 files.")
    parser.add_argument("--features-dir", help="Directory expected to contain CLAM h5_files/ and pt_files/ outputs.")
    parser.add_argument("--dataset-csv", help="Dataset CSV with case_id, slide_id, and label columns.")
    parser.add_argument("--heatmap-config", help="Heatmap YAML config to validate with the heatmap sub-skill helper.")
    parser.add_argument("--checkpoint", help="Model checkpoint path used for evaluation or heatmaps.")
    args = parser.parse_args()

    if args.stage:
        print(f"Route: read {STAGES[args.stage]}")
    else:
        print("Route: choose a stage with --stage or read SKILL.md route bullets.")

    checks = [
        ("slides directory", args.slides_dir),
        ("patch coordinate directory", args.patch_dir),
        ("feature directory", args.features_dir),
        ("dataset CSV", args.dataset_csv),
        ("heatmap config", args.heatmap_config),
        ("checkpoint", args.checkpoint),
    ]
    for label, value in checks:
        print(f"{label}: {existing_path(value)}" + (f" ({value})" if value else ""))

    print("\nNext steps:")
    print("- Use sub-skill helpers for command/config construction before heavy native runs.")
    print("- Confirm OpenSlide, checkpoints, GPU/memory, and output locations before running CLAM scripts.")
    print("- Keep encoder feature dimension aligned: ResNet50/UNI=1024, CONCH=512.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
