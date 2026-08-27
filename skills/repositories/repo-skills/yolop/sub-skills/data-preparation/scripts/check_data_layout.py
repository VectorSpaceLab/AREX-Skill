#!/usr/bin/env python3
"""Validate YOLOP BDD100K-style data roots without importing YOLOP.

Examples:
  python check_data_layout.py --dataset-root /data/yolop-bdd
  python check_data_layout.py --images-root /data/bdd100k/images/100k \
    --det-root /data/det_annotations --da-root /data/bdd_seg_gt --lane-root /data/bdd_lane_gt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

IMAGE_SUFFIX = ".jpg"
MASK_SUFFIX = ".png"
LABEL_SUFFIX = ".json"


def _resolve_roots(args: argparse.Namespace) -> dict[str, Path]:
    if args.dataset_root:
        root = Path(args.dataset_root).expanduser().resolve()
        return {
            "images": root / "images",
            "det": root / "det_annotations",
            "da": root / "da_seg_annotations",
            "lane": root / "ll_seg_annotations",
        }
    needed = {
        "images": args.images_root,
        "det": args.det_root,
        "da": args.da_root,
        "lane": args.lane_root,
    }
    missing = [name for name, value in needed.items() if not value]
    if missing:
        raise SystemExit(f"missing roots for {', '.join(missing)}; pass --dataset-root or all explicit roots")
    return {name: Path(value).expanduser().resolve() for name, value in needed.items()}


def _sample(paths: Iterable[Path], limit: int) -> list[Path]:
    return sorted(paths)[: max(0, limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check YOLOP data root layout and file correspondence")
    parser.add_argument("--dataset-root", help="Combined root with images/det_annotations/da_seg_annotations/ll_seg_annotations")
    parser.add_argument("--images-root", help="Image root containing train/ and val/")
    parser.add_argument("--det-root", help="Detection JSON root containing train/ and val/")
    parser.add_argument("--da-root", help="Drivable-area mask root containing train/ and val/")
    parser.add_argument("--lane-root", help="Lane-line mask root containing train/ and val/")
    parser.add_argument("--splits", nargs="+", default=["train", "val"], help="Split names to check")
    parser.add_argument("--max-samples", type=int, default=20, help="Max drivable mask stems to check per split")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    roots = _resolve_roots(args)
    summary: dict[str, object] = {"roots": {k: str(v) for k, v in roots.items()}, "splits": {}, "errors": []}
    errors: list[str] = []

    for split in args.splits:
        split_summary: dict[str, object] = {}
        dirs = {name: root / split for name, root in roots.items()}
        for name, directory in dirs.items():
            split_summary[f"{name}_dir"] = str(directory)
            if not directory.is_dir():
                errors.append(f"{split}: missing {name} directory {directory}")

        da_dir = dirs["da"]
        if not da_dir.is_dir():
            summary["splits"][split] = split_summary  # type: ignore[index]
            continue

        masks = _sample(da_dir.glob(f"*{MASK_SUFFIX}"), args.max_samples)
        split_summary["sampled_masks"] = len(masks)
        missing_pairs: list[str] = []
        malformed_json: list[str] = []
        for mask in masks:
            stem = mask.stem
            expected = {
                "image": dirs["images"] / f"{stem}{IMAGE_SUFFIX}",
                "det": dirs["det"] / f"{stem}{LABEL_SUFFIX}",
                "lane": dirs["lane"] / f"{stem}{MASK_SUFFIX}",
            }
            for kind, path in expected.items():
                if not path.is_file():
                    missing_pairs.append(f"{stem}: missing {kind} {path}")
            det_path = expected["det"]
            if det_path.is_file():
                try:
                    label = json.loads(det_path.read_text())
                    _ = label["frames"][0]["objects"]
                except Exception as exc:  # pragma: no cover - diagnostic path
                    malformed_json.append(f"{det_path.name}: {exc}")

        split_summary["missing_pairs"] = missing_pairs
        split_summary["malformed_json"] = malformed_json
        if not masks:
            errors.append(f"{split}: no drivable mask PNGs found in {da_dir}")
        errors.extend(f"{split}: {item}" for item in missing_pairs[:10])
        errors.extend(f"{split}: malformed {item}" for item in malformed_json[:10])
        summary["splits"][split] = split_summary  # type: ignore[index]

    summary["errors"] = errors
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for name, root in roots.items():
            print(f"{name}: {root}")
        for split, split_summary in summary["splits"].items():  # type: ignore[union-attr]
            print(f"split {split}: sampled_masks={split_summary.get('sampled_masks', 0)}")  # type: ignore[attr-defined]
        if errors:
            print("ERRORS:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
        else:
            print("YOLOP data layout check passed for sampled masks")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
