#!/usr/bin/env python3
"""Validate common FCOS dataset directory layouts without reading large data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def exists(root: Path, rel: str):
    p = root / rel
    return {"path": rel, "exists": p.exists(), "is_dir": p.is_dir(), "is_file": p.is_file()}


def main() -> int:
    p = argparse.ArgumentParser(description="Validate COCO, VOC, or Cityscapes layout for FCOS")
    p.add_argument("--kind", choices=["coco", "voc", "cityscapes"], required=True)
    p.add_argument("--root", required=True, help="Dataset root to validate")
    args = p.parse_args()
    root = Path(args.root)
    checks = []
    if args.kind == "coco":
        for rel in ["coco/annotations", "coco/train2014", "coco/val2014"]:
            checks.append(exists(root, rel))
        for rel in ["coco/annotations/instances_train2014.json", "coco/annotations/instances_minival2014.json", "coco/annotations/instances_valminusminival2014.json"]:
            checks.append(exists(root, rel))
    elif args.kind == "voc":
        for rel in ["JPEGImages", "Annotations"]:
            checks.append(exists(root, rel))
    else:
        for rel in ["images", "annotations", "annotations/instancesonly_filtered_gtFine_train.json", "annotations/instancesonly_filtered_gtFine_val.json"]:
            checks.append(exists(root, rel))
    ok = root.exists() and all(c["exists"] for c in checks)
    print(json.dumps({"kind": args.kind, "root": str(root), "ok": ok, "checks": checks}, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
