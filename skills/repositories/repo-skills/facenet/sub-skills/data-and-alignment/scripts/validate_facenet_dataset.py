#!/usr/bin/env python3
"""Validate Facenet class-folder datasets and optional LFW pairs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def validate_dataset(root: Path, min_images: int) -> Dict[str, object]:
    classes: List[Dict[str, object]] = []
    problems: List[str] = []
    if not root.exists():
        return {"ok": False, "problems": [f"dataset root does not exist: {root}"], "classes": []}
    class_dirs = sorted([p for p in root.iterdir() if p.is_dir()])
    if not class_dirs:
        problems.append("no immediate class/identity directories found")
    for class_dir in class_dirs:
        images = sorted([p for p in class_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS])
        non_images = sorted([p.name for p in class_dir.iterdir() if p.is_file() and p.suffix.lower() not in IMAGE_EXTS])
        if len(images) < min_images:
            problems.append(f"{class_dir.name}: only {len(images)} image(s), expected at least {min_images}")
        classes.append({"name": class_dir.name, "images": len(images), "non_image_files": non_images[:20]})
    return {"ok": not problems, "problems": problems, "classes": classes}


def add_extension(base: Path):
    for suffix in (".jpg", ".png"):
        candidate = base.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def validate_pairs(pairs_file: Path, lfw_dir: Path) -> Dict[str, object]:
    missing: List[Dict[str, str]] = []
    rows = 0
    if not pairs_file.exists():
        return {"ok": False, "pairs": 0, "missing": [{"row": "0", "path": str(pairs_file), "reason": "pairs file missing"}]}
    lines = pairs_file.read_text().splitlines()[1:]
    for index, line in enumerate(lines, start=2):
        if not line.strip():
            continue
        fields = line.split()
        rows += 1
        refs = []
        if len(fields) == 3:
            refs = [(fields[0], fields[1]), (fields[0], fields[2])]
        elif len(fields) == 4:
            refs = [(fields[0], fields[1]), (fields[2], fields[3])]
        else:
            missing.append({"row": str(index), "path": line, "reason": "expected 3 or 4 columns"})
            continue
        for name, number in refs:
            base = lfw_dir / name / f"{name}_{int(number):04d}"
            if add_extension(base) is None:
                missing.append({"row": str(index), "path": str(base) + ".[jpg|png]", "reason": "referenced image missing"})
    return {"ok": not missing, "pairs": rows, "missing": missing[:100], "missing_count": len(missing)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Facenet class-folder dataset and optional LFW pairs.")
    parser.add_argument("data_dir", type=Path, help="Class-folder dataset root.")
    parser.add_argument("--min-images-per-class", type=int, default=1)
    parser.add_argument("--lfw-pairs", type=Path, help="Optional LFW pairs file to validate.")
    parser.add_argument("--lfw-dir", type=Path, help="Aligned LFW root used by the pairs file.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {"dataset": validate_dataset(args.data_dir, args.min_images_per_class)}
    if args.lfw_pairs or args.lfw_dir:
        if not (args.lfw_pairs and args.lfw_dir):
            payload["pairs"] = {"ok": False, "missing": [], "problem": "provide both --lfw-pairs and --lfw-dir"}
        else:
            payload["pairs"] = validate_pairs(args.lfw_pairs, args.lfw_dir)
    ok = payload["dataset"]["ok"] and payload.get("pairs", {"ok": True}).get("ok", False)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Dataset OK: {payload['dataset']['ok']} classes={len(payload['dataset']['classes'])}")
        for problem in payload["dataset"].get("problems", []):
            print(f"DATASET PROBLEM: {problem}")
        if "pairs" in payload:
            print(f"Pairs OK: {payload['pairs'].get('ok')} pairs={payload['pairs'].get('pairs', 0)} missing={payload['pairs'].get('missing_count', 0)}")
            for item in payload["pairs"].get("missing", [])[:20]:
                print(f"PAIR PROBLEM row {item.get('row')}: {item.get('path')} ({item.get('reason')})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
