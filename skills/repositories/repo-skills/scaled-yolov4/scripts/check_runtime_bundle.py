#!/usr/bin/env python3
"""Verify that the generated ScaledYOLOv4 skill contains its runtime mirror."""

from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = [
    "README.md",
    "detect.py",
    "test.py",
    "train.py",
    "models/__init__.py",
    "models/common.py",
    "models/experimental.py",
    "models/export.py",
    "models/yolo.py",
    "models/yolov4-csp.yaml",
    "models/yolov4-p5.yaml",
    "models/yolov4-p6.yaml",
    "models/yolov4-p7.yaml",
    "utils/__init__.py",
    "utils/activations.py",
    "utils/datasets.py",
    "utils/general.py",
    "utils/google_utils.py",
    "utils/torch_utils.py",
    "data/coco.yaml",
    "data/demo.yaml",
    "data/hyp.finetune.yaml",
    "data/hyp.scratch.yaml",
    "demo/images/train/img1.png",
    "demo/images/val/img2.png",
    "demo/labels/train/img1.txt",
    "demo/labels/val/img2.txt",
]


def default_skill_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "runtime").is_dir() and (parent / "SKILL.md").is_file():
            return parent
    raise RuntimeError("could not locate scaled-yolov4 skill root")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=None, help="generated skill root; defaults to this script's skill root")
    args = parser.parse_args()

    skill_root = (args.skill_root or default_skill_root()).expanduser().resolve()
    runtime = skill_root / "runtime"
    missing = [rel for rel in REQUIRED if not (runtime / rel).is_file()]
    print(f"skill_root={skill_root}")
    print(f"runtime={runtime}")
    print(f"required_files={len(REQUIRED)}")
    if missing:
        print("missing:")
        for rel in missing:
            print(f"- {rel}")
        return 1
    print("runtime bundle complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
