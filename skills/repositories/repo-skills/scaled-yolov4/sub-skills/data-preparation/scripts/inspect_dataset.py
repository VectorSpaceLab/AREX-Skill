#!/usr/bin/env python3
"""Inspect a ScaledYOLOv4 dataset YAML and a few sampled labels.

This helper is intentionally lightweight: it validates the YAML structure,
resolves split sources, checks a small sample of image paths, and optionally
peeks at a few matching YOLO label files. It does not build a full dataloader
or touch the training loop. With no arguments it inspects the bundled demo
YAML in this skill's ``runtime/`` mirror; custom absolute YAML files resolve
split paths beside that YAML unless ``--data-root`` is supplied.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml

IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dng"}
VIDEO_SUFFIXES = {".mov", ".avi", ".mp4", ".mpg", ".mpeg", ".m4v", ".wmv", ".mkv"}


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "data" / "coco.yaml").is_file() and (candidate / "utils" / "datasets.py").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing data/coco.yaml")


def resolve_path(base: Path, raw: str) -> Path:
    path = Path(raw.strip())
    if path.is_absolute():
        return path
    return (base / path).resolve()


def read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("dataset YAML must contain a mapping")
    return data


def sample_image_entries(source: Path, max_samples: int) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".txt":
        entries: list[Path] = []
        for raw in source.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = (source.parent / candidate).resolve()
            entries.append(candidate)
        return entries[:max_samples]

    if source.is_dir():
        files = [p for p in sorted(source.iterdir()) if p.suffix.lower() in IMAGE_SUFFIXES]
        return files[:max_samples]

    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES | VIDEO_SUFFIXES:
        return [source]

    return []


def derive_label_path(image_path: Path) -> Path:
    parts = list(image_path.parts)
    if "images" in parts:
        idx = len(parts) - 1 - parts[::-1].index("images")
        parts[idx] = "labels"
        return Path(*parts).with_suffix(".txt")

    if image_path.parent.name:
        return image_path.parent.parent / "labels" / f"{image_path.stem}.txt"

    return image_path.with_suffix(".txt")


def check_label_file(label_path: Path) -> list[str]:
    issues: list[str] = []
    if not label_path.is_file():
        issues.append(f"missing label file: {label_path}")
        return issues

    for line_no, raw in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split()
        if len(parts) != 5:
            issues.append(f"{label_path}:{line_no} has {len(parts)} columns, expected 5")
            continue
        try:
            cls = int(float(parts[0]))
            coords = [float(x) for x in parts[1:]]
        except ValueError:
            issues.append(f"{label_path}:{line_no} has non-numeric values")
            continue
        if cls < 0:
            issues.append(f"{label_path}:{line_no} has a negative class id")
        for value in coords:
            if value < -1e-6 or value > 1 + 1e-6:
                issues.append(f"{label_path}:{line_no} has out-of-range normalized coordinates")
                break
    return issues


def summarize_split(name: str, source: Path, max_samples: int, require_labels: bool) -> tuple[int, list[str]]:
    issues: list[str] = []
    sample_count = 0

    if source.is_file() and source.suffix.lower() == ".txt":
        lines = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"{name}: text list with {len(lines)} entries -> {source}")
        samples = sample_image_entries(source, max_samples)
        for image_path in samples:
            sample_count += 1
            if not image_path.exists():
                issues.append(f"missing image file: {image_path}")
                continue
            if require_labels:
                label_path = derive_label_path(image_path)
                issues.extend(check_label_file(label_path))
        return sample_count, issues

    if source.is_dir():
        images = [p for p in sorted(source.iterdir()) if p.suffix.lower() in IMAGE_SUFFIXES]
        videos = [p for p in sorted(source.iterdir()) if p.suffix.lower() in VIDEO_SUFFIXES]
        print(f"{name}: directory with {len(images)} images and {len(videos)} videos -> {source}")
        samples = images[:max_samples]
        for image_path in samples:
            sample_count += 1
            if require_labels:
                label_path = derive_label_path(image_path)
                issues.extend(check_label_file(label_path))
        return sample_count, issues

    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES | VIDEO_SUFFIXES:
        print(f"{name}: single media file -> {source}")
        sample_count = 1
        if require_labels:
            issues.extend(check_label_file(derive_label_path(source)))
        return sample_count, issues

    issues.append(f"unsupported source type: {source}")
    return sample_count, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="source root used to resolve default bundled YAML paths")
    parser.add_argument("--yaml", type=Path, default=Path("data/demo.yaml"), help="dataset YAML to inspect")
    parser.add_argument("--data-root", type=Path, default=None, help="optional base directory for resolving split paths inside the YAML")
    parser.add_argument("--max-samples", type=int, default=5, help="sample limit per split")
    parser.add_argument("--require-labels", action="store_true", help="also inspect a few matching YOLO label files")
    args = parser.parse_args()

    runtime_root = default_runtime_root()
    raw_yaml = args.yaml.expanduser()
    if args.repo_root is None:
        repo_root = raw_yaml.parent.resolve() if raw_yaml.is_absolute() else runtime_root
    else:
        repo_root = args.repo_root.expanduser().resolve()
    yaml_path = raw_yaml
    if not yaml_path.is_absolute():
        yaml_path = (repo_root / yaml_path).resolve()
    data_root = args.data_root.expanduser().resolve() if args.data_root else (yaml_path.parent if args.repo_root is None and raw_yaml.is_absolute() else repo_root)
    if not yaml_path.is_file():
        parser.error(f"dataset YAML not found: {yaml_path}")

    data = read_yaml(yaml_path)
    issues: list[str] = []

    print(f"dataset: {yaml_path}")
    print(f"keys: {', '.join(sorted(data.keys()))}")

    nc = data.get("nc")
    names = data.get("names", [])
    if isinstance(names, list):
        name_count = len(names)
    else:
        name_count = -1
        issues.append("names must be a list")

    if isinstance(nc, int) and name_count != -1 and nc != name_count:
        issues.append(f"nc={nc} does not match len(names)={name_count}")
    elif isinstance(nc, int):
        print(f"class-count: nc={nc}, names={name_count}")
    else:
        issues.append("nc must be an integer")

    for split in ("train", "val", "test"):
        raw = data.get(split)
        if not raw:
            continue
        source = resolve_path(data_root, str(raw))
        if not source.exists():
            issues.append(f"{split} source does not exist: {source}")
            continue
        sample_count, split_issues = summarize_split(split, source, args.max_samples, args.require_labels)
        print(f"  sampled {sample_count} item(s) from {split}")
        issues.extend(split_issues)

    if issues:
        print("issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("dataset inspection passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
