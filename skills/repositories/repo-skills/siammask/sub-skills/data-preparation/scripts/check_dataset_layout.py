#!/usr/bin/env python3
"""Read-only checks for SiamMask dataset layouts.

The checker validates expected files/directories for benchmark and training data
without downloading, cropping, or modifying anything. It is intentionally
conservative: missing optional datasets are warnings unless --strict is set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DATASETS = ["vot", "davis", "ytb_vos", "coco", "det", "vid", "training"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect SiamMask data directory layouts without mutation.")
    p.add_argument("--data-root", default="data", help="Path to the checkout-local data directory or equivalent data root.")
    p.add_argument("--dataset", choices=DATASETS, action="append", help="Dataset family to check. Repeat to check multiple families. Defaults to all.")
    p.add_argument("--strict", action="store_true", help="Exit non-zero if any expected item is missing.")
    return p.parse_args()


def exists(path: Path) -> dict[str, object]:
    return {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir(), "is_file": path.is_file()}


def check_vot(root: Path) -> dict[str, object]:
    years = ["VOT2016", "VOT2018", "VOT2019"]
    return {
        "json_files": [exists(root / f"{year}.json") for year in years],
        "datasets": [
            {
                "name": year,
                "directory": exists(root / year),
                "list_txt": exists(root / year / "list.txt"),
                "sample_groundtruth": bool(list((root / year).glob("*/groundtruth.txt"))) if (root / year).exists() else False,
            }
            for year in years
        ],
    }


def check_davis(root: Path) -> dict[str, object]:
    base = root / "DAVIS"
    return {
        "directory": exists(base),
        "image_sets": [exists(base / "ImageSets" / year / "val.txt") for year in ["2016", "2017"]],
        "annotations": exists(base / "Annotations" / "480p"),
        "images": exists(base / "JPEGImages" / "480p"),
        "compat_symlinks": [exists(root / "DAVIS2016"), exists(root / "DAVIS2017")],
    }


def check_ytb(root: Path) -> dict[str, object]:
    base = root / "ytb_vos"
    return {
        "directory": exists(base),
        "raw_or_valid_meta": [exists(base / "train" / "meta.json"), exists(base / "valid" / "meta.json")],
        "training_json": exists(base / "train.json"),
        "crop511": exists(base / "crop511"),
    }


def check_coco(root: Path) -> dict[str, object]:
    base = root / "coco"
    return {
        "directory": exists(base),
        "annotations": [exists(base / "annotations" / f"instances_{split}.json") for split in ["train2017", "val2017"]],
        "images": [exists(base / split) for split in ["train2017", "val2017"]],
        "indexes": [exists(base / f"{split}.json") for split in ["train2017", "val2017"]],
        "crop511": exists(base / "crop511"),
        "local_pycocotools": exists(base / "pycocotools"),
    }


def check_det(root: Path) -> dict[str, object]:
    base = root / "det"
    return {
        "directory": exists(base),
        "ilsvrc": exists(base / "ILSVRC2015"),
        "train_json": exists(base / "train.json"),
        "crop511": exists(base / "crop511"),
    }


def check_vid(root: Path) -> dict[str, object]:
    base = root / "vid"
    return {
        "directory": exists(base),
        "ilsvrc": exists(base / "ILSVRC2015"),
        "raw_vid_json": exists(base / "vid.json"),
        "train_json": exists(base / "train.json"),
        "val_json": exists(base / "val.json"),
        "crop511": exists(base / "crop511"),
    }


def has_missing(obj: object) -> bool:
    if isinstance(obj, dict):
        if "exists" in obj and obj["exists"] is False:
            return True
        return any(has_missing(v) for v in obj.values())
    if isinstance(obj, list):
        return any(has_missing(v) for v in obj)
    return False


def main() -> int:
    args = parse_args()
    root = Path(args.data_root).expanduser().resolve()
    selected = args.dataset or DATASETS
    report: dict[str, object] = {"data_root": str(root), "checks": {}}
    if "vot" in selected:
        report["checks"]["vot"] = check_vot(root)
    if "davis" in selected:
        report["checks"]["davis"] = check_davis(root)
    if "ytb_vos" in selected:
        report["checks"]["ytb_vos"] = check_ytb(root)
    if "coco" in selected or "training" in selected:
        report["checks"]["coco"] = check_coco(root)
    if "det" in selected or "training" in selected:
        report["checks"]["det"] = check_det(root)
    if "vid" in selected or "training" in selected:
        report["checks"]["vid"] = check_vid(root)
    if "training" in selected:
        report["checks"]["ytb_vos"] = check_ytb(root)
    report["status"] = "missing" if has_missing(report["checks"]) else "ok"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if args.strict and report["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
