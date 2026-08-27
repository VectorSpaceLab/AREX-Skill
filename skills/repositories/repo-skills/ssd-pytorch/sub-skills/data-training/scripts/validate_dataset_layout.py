#!/usr/bin/env python3
"""Validate SSD.PyTorch VOC or COCO dataset skeletons without downloading data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def exists(path: Path, kind: str = "path") -> dict[str, Any]:
    return {"path": str(path), "exists": path.exists(), "kind": kind}


def voc_checks(root: Path, require_train: bool, require_test: bool) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    years: list[tuple[str, str]] = []
    if require_train or not require_test:
        years.extend([("2007", "trainval"), ("2012", "trainval")])
    if require_test:
        years.append(("2007", "test"))
    seen: set[tuple[str, str]] = set()
    for year, split in years:
        if (year, split) in seen:
            continue
        seen.add((year, split))
        base = root / f"VOC{year}"
        checks.extend(
            [
                exists(base, "voc-year-dir"),
                exists(base / "Annotations", "annotations-dir"),
                exists(base / "JPEGImages", "images-dir"),
                exists(base / "ImageSets" / "Main" / f"{split}.txt", "split-file"),
            ]
        )
    return checks


def coco_checks(root: Path, require_train: bool, require_test: bool) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [exists(root / "coco_labels.txt", "label-map")]
    if require_train or not require_test:
        checks.extend(
            [
                exists(root / "images" / "trainval35k", "train-images-dir"),
                exists(root / "annotations" / "instances_trainval35k.json", "train-annotations-json"),
            ]
        )
    if require_test:
        checks.extend(
            [
                exists(root / "images" / "val2014", "val-images-dir"),
                exists(root / "annotations" / "instances_val2014.json", "val-annotations-json"),
            ]
        )
    pyapi = root / "PythonAPI"
    checks.append({"path": str(pyapi), "exists": pyapi.exists(), "kind": "optional-pythonapi", "note": "optional if pycocotools is installed"})
    return checks


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [c for c in checks if not c.get("exists") and not str(c.get("kind", "")).startswith("optional")]
    optional_missing = [c for c in checks if not c.get("exists") and str(c.get("kind", "")).startswith("optional")]
    return {"ok": not missing, "missing_required": missing, "missing_optional": optional_missing, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VOC/COCO directory skeletons for ssd.pytorch")
    parser.add_argument("--dataset", choices=("voc", "coco"), required=True)
    parser.add_argument("--root", required=True, help="VOCdevkit root for VOC or COCO root for COCO")
    parser.add_argument("--require-train", action="store_true", help="require training split files")
    parser.add_argument("--require-test", action="store_true", help="require test/eval split files")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if args.dataset == "voc":
        checks = voc_checks(root, args.require_train, args.require_test)
    else:
        checks = coco_checks(root, args.require_train, args.require_test)
    report = summarize(checks)
    report.update({"dataset": args.dataset, "root": str(root), "note": "No downloads or dataset mutations were performed."})
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
