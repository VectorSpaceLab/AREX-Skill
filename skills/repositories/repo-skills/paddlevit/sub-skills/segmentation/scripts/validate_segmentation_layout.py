#!/usr/bin/env python3
"""Read-only preflight for PaddleViT semantic-segmentation dataset roots.

This script intentionally has no dependency on PaddleViT, Paddle, downloaded
weights, or the original checkout. It never creates, modifies, or deletes a
file. It checks the layouts implemented by the built-in dataset classes and
can optionally inspect a bounded number of image/mask pairs with Pillow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.pairs: List[Tuple[Path, Path]] = []
        self.counts: Dict[str, int] = {}

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_pairs(self, pairs: Iterable[Tuple[Path, Path]], name: str) -> None:
        materialized = list(pairs)
        self.pairs.extend(materialized)
        self.counts[name] = len(materialized)
        if not materialized:
            self.error(f"{name}: no image/label pairs found")


def mode_list(dataset: str, mode: str) -> Sequence[str]:
    if mode != "all":
        return (mode,)
    if dataset in {"PascalContext", "ADE20K", "custom"}:
        return ("train", "val")
    return ("train", "val", "test")


def require_dir(path: Path, label: str, report: Report) -> bool:
    if not path.is_dir():
        report.error(f"{label} directory is missing: {path}")
        return False
    return True


def read_ids(path: Path, report: Report) -> List[str]:
    if not path.is_file():
        report.error(f"split list is missing: {path}")
        return []
    ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(ids) != len(set(ids)):
        report.error(f"split list contains duplicate ids: {path}")
    return ids


def check_pascal(root: Path, mode: str, report: Report) -> None:
    if mode == "test":
        report.error("PascalContext built-in loader supports train/val, not test")
        return
    image_dir = root / "JPEGImages"
    label_dir = root / "SegmentationClassContext"
    split = root / "ImageSets" / "SegmentationContext" / f"{mode}.txt"
    if not (require_dir(image_dir, "PascalContext JPEGImages", report)
            and require_dir(label_dir, "PascalContext SegmentationClassContext", report)):
        return
    pairs = []
    for item_id in read_ids(split, report):
        image = image_dir / f"{item_id}.jpg"
        label = label_dir / f"{item_id}.png"
        if not image.is_file():
            report.error(f"PascalContext {mode}: image listed but missing: {image}")
        if not label.is_file():
            report.error(f"PascalContext {mode}: label listed but missing: {label}")
        if image.is_file() and label.is_file():
            pairs.append((image, label))
    report.add_pairs(pairs, f"PascalContext/{mode}")


def check_ade(root: Path, mode: str, report: Report) -> None:
    if mode == "test":
        report.error("ADE20K built-in loader supports train/val, not test")
        return
    physical = "training" if mode == "train" else "validation"
    image_dir = root / "images" / physical
    label_dir = root / "annotations" / physical
    if not (require_dir(image_dir, f"ADE20K images/{physical}", report)
            and require_dir(label_dir, f"ADE20K annotations/{physical}", report)):
        return
    images = sorted(image_dir.glob("*.jpg"))
    pairs = []
    if not images:
        report.error(f"ADE20K/{mode}: no lowercase .jpg images found (source replaces .jpg with .png)")
    for image in images:
        label = label_dir / f"{image.stem}.png"
        if not label.is_file():
            report.error(f"ADE20K/{mode}: label missing for {image.name}: {label}")
        else:
            pairs.append((image, label))
    unexpected = [p for p in label_dir.glob("*") if p.is_file() and p.suffix.lower() == ".png"
                  and p.stem not in {image.stem for image in images}]
    if unexpected:
        report.warning(f"ADE20K/{mode}: {len(unexpected)} annotation PNGs have no matching .jpg")
    report.add_pairs(pairs, f"ADE20K/{mode}")


def check_cityscapes(root: Path, mode: str, report: Report) -> None:
    image_dir = root / "leftImg8bit" / mode
    label_dir = root / "gtFine" / mode
    if not (require_dir(image_dir, f"Cityscapes leftImg8bit/{mode}", report)
            and require_dir(label_dir, f"Cityscapes gtFine/{mode}", report)):
        return
    images = sorted(image_dir.rglob("*_leftImg8bit.png"))
    labels = sorted(label_dir.rglob("*_gtFine_labelTrainIds.png"))

    def relative_stem(path: Path, base: Path, suffix: str) -> str:
        # Preserve the city-relative path; basenames alone collide across
        # Cityscapes cities and can hide a bad pairing.
        relative = path.relative_to(base).as_posix()
        return relative[: -len(suffix)]

    image_map = {relative_stem(p, image_dir, "_leftImg8bit.png"): p for p in images}
    label_map = {relative_stem(p, label_dir, "_gtFine_labelTrainIds.png"): p for p in labels}
    missing_labels = sorted(set(image_map) - set(label_map))
    missing_images = sorted(set(label_map) - set(image_map))
    for key in missing_labels:
        report.error(f"Cityscapes/{mode}: label missing for {key}")
    for key in missing_images:
        report.error(f"Cityscapes/{mode}: label has no image for {key}")
    pairs = [(image_map[key], label_map[key]) for key in sorted(set(image_map) & set(label_map))]
    if images and labels and len(images) != len(labels):
        report.error(f"Cityscapes/{mode}: image count {len(images)} != label count {len(labels)}")
    report.add_pairs(pairs, f"Cityscapes/{mode}")


def check_trans10k(root: Path, mode: str, report: Report) -> None:
    physical = "validation" if mode == "val" else mode
    image_dir = root / physical / "images"
    label_dir = root / physical / "masks_12"
    if not (require_dir(image_dir, f"Trans10kV2 {physical}/images", report)
            and require_dir(label_dir, f"Trans10kV2 {physical}/masks_12", report)):
        return
    images = sorted(image_dir.glob("*.jpg"))
    labels = sorted(label_dir.glob("*_mask.png"))
    image_map = {p.stem: p for p in images}
    label_map = {p.name[: -len("_mask.png")]: p for p in labels}
    missing_labels = sorted(set(image_map) - set(label_map))
    missing_images = sorted(set(label_map) - set(image_map))
    for key in missing_labels:
        report.error(f"Trans10kV2/{mode}: mask missing for {key}")
    for key in missing_images:
        report.error(f"Trans10kV2/{mode}: mask has no image for {key}")
    pairs = [(image_map[key], label_map[key]) for key in sorted(set(image_map) & set(label_map))]
    if images and labels and len(images) != len(labels):
        report.error(f"Trans10kV2/{mode}: image count {len(images)} != mask count {len(labels)}")
    report.add_pairs(pairs, f"Trans10kV2/{mode}")


def check_custom(root: Path, mode: str, report: Report) -> None:
    if mode == "test":
        report.error("tutorial custom layout documents training/validation only; test needs a registered implementation")
        return
    physical = "training" if mode == "train" else "validation"
    image_dir = root / "images" / physical
    label_dir = root / "annotations" / physical
    if not (require_dir(image_dir, f"custom images/{physical}", report)
            and require_dir(label_dir, f"custom annotations/{physical}", report)):
        return
    images = sorted(p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    labels = sorted(p for p in label_dir.iterdir() if p.is_file())
    label_map = {p.stem: p for p in labels}
    pairs = []
    for image in images:
        label = label_map.get(image.stem)
        if label is None:
            report.error(f"custom/{mode}: no label with stem {image.stem!r}")
        else:
            pairs.append((image, label))
    image_stems = {p.stem for p in images}
    for label in labels:
        if label.stem not in image_stems:
            report.error(f"custom/{mode}: annotation has no image with stem {label.stem!r}")
    report.add_pairs(pairs, f"custom/{mode}")


def inspect_pairs(pairs: Sequence[Tuple[Path, Path]], dataset: str,
                  num_classes: Optional[int], ignore_index: int,
                  max_files: int, report: Report) -> None:
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        report.warning(f"--check-labels requested but Pillow is unavailable: {exc}")
        return
    if max_files < 1:
        report.error("--max-files must be at least 1")
        return
    seen = set()
    for image_path, label_path in pairs[:max_files]:
        try:
            with Image.open(image_path) as image, Image.open(label_path) as label:
                if image.size != label.size:
                    report.error(f"dimension mismatch: {image_path} {image.size} vs {label_path} {label.size}")
                values = set(label.getdata())
                if values and any(not isinstance(value, int) for value in values):
                    report.error(f"label is not single-channel/indexed: {label_path}")
                    continue
                seen.update(values)
                if num_classes is not None:
                    allowed = set(range(num_classes)) | {ignore_index}
                    if dataset == "ADE20K":
                        # The built-in loader subtracts one from raw ADE20K ids.
                        allowed |= {num_classes}
                    invalid = sorted(int(v) for v in values if v not in allowed)
                    if invalid:
                        report.error(f"label ids outside expected range in {label_path}: {invalid[:12]}")
        except Exception as exc:
            report.error(f"cannot open image/label pair {image_path}, {label_path}: {exc}")
    if seen:
        report.info.append(f"sampled {min(max_files, len(pairs))} labels; observed ids: {sorted(seen)[:30]}")


def build_report(args: argparse.Namespace) -> Report:
    report = Report()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        report.error(f"dataset root is missing or not a directory: {root}")
        return report
    if args.num_classes is not None and args.num_classes < 1:
        report.error("--num-classes must be positive")
        return report
    for mode in mode_list(args.dataset, args.mode):
        if args.dataset == "PascalContext":
            check_pascal(root, mode, report)
        elif args.dataset == "ADE20K":
            check_ade(root, mode, report)
        elif args.dataset == "Cityscapes":
            check_cityscapes(root, mode, report)
        elif args.dataset == "Trans10kV2":
            check_trans10k(root, mode, report)
        else:
            check_custom(root, mode, report)
    if args.check_labels:
        inspect_pairs(report.pairs, args.dataset, args.num_classes,
                      args.ignore_index, args.max_files, report)
    return report


def print_report(report: Report, as_json: bool) -> None:
    payload = {
        "ok": not report.errors,
        "errors": report.errors,
        "warnings": report.warnings,
        "info": report.info,
        "counts": report.counts,
        "pairs_checked": len(report.pairs),
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for line in report.info:
        print(f"INFO: {line}")
    for line in report.warnings:
        print(f"WARNING: {line}")
    for line in report.errors:
        print(f"ERROR: {line}")
    print(f"Summary: {'PASS' if not report.errors else 'FAIL'}; "
          f"pairs={len(report.pairs)}; splits={report.counts}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only validation of PaddleViT semantic-segmentation dataset layouts.")
    parser.add_argument("--dataset", required=True,
                        choices=["PascalContext", "ADE20K", "Cityscapes", "Trans10kV2", "custom"],
                        help="dataset factory key or the tutorial custom layout")
    parser.add_argument("--root", required=True, help="dataset root to inspect")
    parser.add_argument("--mode", choices=["train", "val", "test", "all"], default="all",
                        help="split to inspect; all checks train/val and optional test as appropriate")
    parser.add_argument("--num-classes", type=int,
                        help="optional class count for sampled label-id range checks")
    parser.add_argument("--ignore-index", type=int, default=255,
                        help="ignored label id for --check-labels (default: 255)")
    parser.add_argument("--check-labels", action="store_true",
                        help="also open a bounded sample, compare dimensions, and inspect ids (read-only)")
    parser.add_argument("--max-files", type=int, default=32,
                        help="maximum pairs to open with --check-labels (default: 32)")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    print_report(report, args.json)
    return 0 if not report.errors else 1


if __name__ == "__main__":
    sys.exit(main())
